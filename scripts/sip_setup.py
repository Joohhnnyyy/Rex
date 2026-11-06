"""T-30: phone calls from Rex through Twilio into LiveKit.

Trial account (Elastic SIP Trunking is blocked on trial, error 20003): Twilio Programmable Voice places the
call and, once answered, <Dial><Sip>s it into a LiveKit inbound trunk; a dispatch rule puts it in a room.

    uv run --env-file .env python scripts/sip_setup.py inbound          # once: LiveKit inbound trunk + rule
    uv run --env-file .env python scripts/sip_setup.py call +91XXXXXXXXXX

Paid account (Elastic SIP Trunking -> LiveKit outbound trunk, LiveKit dials directly):

    uv run --env-file .env python scripts/sip_setup.py trunk-setup      # prints LIVEKIT_SIP_TRUNK_ID for .env
    uv run --env-file .env python scripts/sip_setup.py trunk-call +91XXXXXXXXXX

Env: TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID/SECRET (or TWILIO_AUTH_TOKEN), TWILIO_NUMBER (the Twilio number,
E.164), LIVEKIT_URL/API_KEY/API_SECRET, and for the trial path LIVEKIT_SIP_URI (LiveKit Cloud -> Settings ->
SIP URI, e.g. sip:abc123.sip.livekit.cloud). SIP passwords are never printed: the trial one is derived from
LIVEKIT_API_SECRET, the trunk one is random and lives only in Twilio and LiveKit. Trial: the called number
must be a Verified Caller ID and the country enabled under Voice -> Geo permissions.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import secrets
import string
import sys
from urllib.parse import urlencode
from xml.sax.saxutils import quoteattr

import httpx
from livekit import api

NAME = "rex-outbound"
INBOUND = "rex-twilio-in"
ROOM = "rex-call-test"
TRUNKING = "https://trunking.twilio.com/v1"


def twilio() -> httpx.Client:
    sid = os.environ.get("TWILIO_ACCOUNT_SID") or sys.exit("TWILIO_ACCOUNT_SID (AC...) is empty in .env")
    user = os.environ.get("TWILIO_API_KEY_SID") or sid
    pw = os.environ.get("TWILIO_API_KEY_SECRET") or os.environ["TWILIO_AUTH_TOKEN"]
    return httpx.Client(auth=(user, pw), timeout=20)


def account_url() -> str:
    return f"https://api.twilio.com/2010-04-01/Accounts/{os.environ['TWILIO_ACCOUNT_SID']}"


def twilio_number() -> str:
    n = os.environ.get("TWILIO_NUMBER") or sys.exit("TWILIO_NUMBER (your Twilio number, +1...) is empty in .env")
    return n if n.startswith("+") else sys.exit(f"TWILIO_NUMBER must be E.164 with +country code, got {n!r}")


def _ok(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        sys.exit(f"Twilio {r.request.method} {r.request.url.path}: {r.status_code} {r.text[:300]}")
    return r.json()


# --- trial path: Twilio Programmable Voice -> LiveKit inbound trunk ---------------------------------------


def _inbound_password() -> str:
    """Same value on both sides without storing it anywhere: HMAC of the LiveKit secret."""
    return hmac.new(os.environ["LIVEKIT_API_SECRET"].encode(), b"rex-twilio-in", hashlib.sha256).hexdigest()[:32]


async def inbound() -> None:
    number = twilio_number()
    async with api.LiveKitAPI() as lk:
        for t in (await lk.sip.list_inbound_trunk(api.ListSIPInboundTrunkRequest())).items:
            if t.name == INBOUND:
                await lk.sip.delete_trunk(api.DeleteSIPTrunkRequest(sip_trunk_id=t.sip_trunk_id))
        for r in (await lk.sip.list_dispatch_rule(api.ListSIPDispatchRuleRequest())).items:
            if r.name == INBOUND:
                await lk.sip.delete_dispatch_rule(
                    api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=r.sip_dispatch_rule_id)
                )
        info = api.SIPInboundTrunkInfo(
            name=INBOUND, numbers=[number], auth_username="rex", auth_password=_inbound_password()
        )
        trunk = await lk.sip.create_inbound_trunk(api.CreateSIPInboundTrunkRequest(trunk=info))
        rule = api.SIPDispatchRule(dispatch_rule_direct=api.SIPDispatchRuleDirect(room_name=ROOM))
        await lk.sip.create_dispatch_rule(
            api.CreateSIPDispatchRuleRequest(name=INBOUND, rule=rule, trunk_ids=[trunk.sip_trunk_id])
        )
    print(f"LiveKit inbound trunk {trunk.sip_trunk_id} for {number} -> room {ROOM}")


def twiml(number: str) -> str:
    host = os.environ.get("LIVEKIT_SIP_URI") or sys.exit(
        "LIVEKIT_SIP_URI is empty (LiveKit Cloud -> Settings -> SIP URI)"
    )
    host = host.removeprefix("sip:")
    sip = f"sip:{number}@{host};transport=tcp"
    return (
        f'<Response><Dial><Sip username="rex" password={quoteattr(_inbound_password())}>{sip}</Sip></Dial></Response>'
    )


def call(to: str) -> None:
    number = twilio_number()
    with twilio() as tw:
        # Trial rejects inline Twiml (400), so Twilio's own echo twimlet serves it from a URL.
        url = "https://twimlets.com/echo?" + urlencode({"Twiml": twiml(number)})
        c = _ok(tw.post(f"{account_url()}/Calls.json", data={"To": to, "From": number, "Url": url}))
    print(f"calling {to} from {number}: call {c['sid']} status {c['status']}; answer -> joins LiveKit room {ROOM}")


# --- paid path: Elastic SIP trunk -> LiveKit outbound trunk ----------------------------------------------


def _password() -> str:
    # Twilio: >= 12 chars with upper, lower and a digit
    abc = string.ascii_letters + string.digits
    while True:
        p = "".join(secrets.choice(abc) for _ in range(24))
        if any(c.isupper() for c in p) and any(c.islower() for c in p) and any(c.isdigit() for c in p):
            return p


def twilio_trunk(tw: httpx.Client, number: str) -> tuple[str, str, str]:
    """Returns (termination host, sip username, sip password). Recreates the credential each run."""
    acct = account_url()
    trunk = next((t for t in _ok(tw.get(f"{TRUNKING}/Trunks"))["trunks"] if t["friendly_name"] == NAME), None)
    if not trunk:
        domain = f"rex-{secrets.token_hex(4)}.pstn.twilio.com"
        trunk = _ok(tw.post(f"{TRUNKING}/Trunks", data={"FriendlyName": NAME, "DomainName": domain}))
    tsid, host = trunk["sid"], trunk["domain_name"]

    lists = _ok(tw.get(f"{acct}/SIP/CredentialLists.json"))["credential_lists"]
    cl = next((c for c in lists if c["friendly_name"] == NAME), None) or _ok(
        tw.post(f"{acct}/SIP/CredentialLists.json", data={"FriendlyName": NAME})
    )
    user, pw = "rex", _password()
    for c in _ok(tw.get(f"{acct}/SIP/CredentialLists/{cl['sid']}/Credentials.json"))["credentials"]:
        tw.delete(f"{acct}/SIP/CredentialLists/{cl['sid']}/Credentials/{c['sid']}.json")  # 204, no body
    _ok(tw.post(f"{acct}/SIP/CredentialLists/{cl['sid']}/Credentials.json", data={"Username": user, "Password": pw}))
    linked = [c["sid"] for c in _ok(tw.get(f"{TRUNKING}/Trunks/{tsid}/CredentialLists"))["credential_lists"]]
    if cl["sid"] not in linked:
        _ok(tw.post(f"{TRUNKING}/Trunks/{tsid}/CredentialLists", data={"CredentialListSid": cl["sid"]}))

    nums = _ok(tw.get(f"{acct}/IncomingPhoneNumbers.json", params={"PhoneNumber": number}))["incoming_phone_numbers"]
    if not nums:
        sys.exit(f"TWILIO_NUMBER {number} is not a number on this Twilio account")
    if nums[0].get("trunk_sid") != tsid:
        _ok(tw.post(f"{TRUNKING}/Trunks/{tsid}/PhoneNumbers", data={"PhoneNumberSid": nums[0]["sid"]}))
    return host, user, pw


async def trunk_setup() -> None:
    number = twilio_number()
    with twilio() as tw:
        host, user, pw = twilio_trunk(tw, number)
    async with api.LiveKitAPI() as lk:
        for t in (await lk.sip.list_outbound_trunk(api.ListSIPOutboundTrunkRequest())).items:
            if t.name == NAME:
                await lk.sip.delete_trunk(api.DeleteSIPTrunkRequest(sip_trunk_id=t.sip_trunk_id))
        info = api.SIPOutboundTrunkInfo(name=NAME, address=host, numbers=[number], auth_username=user, auth_password=pw)
        t = await lk.sip.create_outbound_trunk(api.CreateSIPOutboundTrunkRequest(trunk=info))
    print(f"Twilio trunk {host} -> LiveKit outbound trunk ready.\nAdd to .env:  LIVEKIT_SIP_TRUNK_ID={t.sip_trunk_id}")


async def trunk_call(to: str) -> None:
    trunk = os.environ.get("LIVEKIT_SIP_TRUNK_ID") or sys.exit("LIVEKIT_SIP_TRUNK_ID missing; run trunk-setup first")
    req = api.CreateSIPParticipantRequest(
        sip_trunk_id=trunk, sip_call_to=to, room_name=ROOM, participant_identity="callee", wait_until_answered=True
    )
    async with api.LiveKitAPI() as lk:
        try:
            p = await lk.sip.create_sip_participant(req)
        except api.TwirpError as e:
            sys.exit(f"call failed: {e.code} {e.message} {e.metadata}")
    print(f"answered: room {ROOM}, participant {p.participant_identity}, call {p.sip_call_id}")


if __name__ == "__main__":
    cmd, args = sys.argv[1:2], sys.argv[2:]
    if cmd == ["inbound"]:
        asyncio.run(inbound())
    elif cmd == ["call"] and len(args) == 1:
        call(args[0])
    elif cmd == ["trunk-setup"]:
        asyncio.run(trunk_setup())
    elif cmd == ["trunk-call"] and len(args) == 1:
        asyncio.run(trunk_call(args[0]))
    else:
        sys.exit(__doc__)

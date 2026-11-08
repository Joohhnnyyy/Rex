import type { MascotState } from './dashboard';
import { BotEngine } from './bloub/engine';
import { EXPRESSIONS, type ExpressionId } from './bloub/expressions';
import { SHAPE_BY_ID } from './bloub/skins';
import { POSES, STATES, type StateId } from './bloub/states';

export type MascotAnimation = StateId;
export type MascotExpression = ExpressionId;
export const ANIMATIONS = STATES.map(({ id }) => id);
export const EXPRESSIONS_LIST: [ExpressionId, string][] = [
  ['neutre', 'Neutral'], ['attentif', 'Attentive'], ['surpris', 'Surprised'],
  ['excite', 'Excited'], ['heureux', 'Happy'], ['hilare', 'Laughing'],
  ['colere', 'Angry'], ['triste', 'Sad'], ['effraye', 'Frightened'],
  ['mefiant', 'Suspicious'], ['confus', 'Confused'], ['curieux', 'Curious'],
  ['fier', 'Proud'], ['timide', 'Shy'], ['blase', 'Bored'], ['somnolent', 'Drowsy'],
];
const LIVE: Record<MascotState, [StateId, ExpressionId]> = {
  idle: ['idle', 'neutre'], listening: ['idle', 'attentif'], thinking: ['thinking', 'curieux'],
  speaking: ['idle', 'excite'], happy: ['idle', 'heureux'], confused: ['idle', 'confus'],
  surprised: ['wide', 'surpris'], error: ['idle', 'colere'], sleeping: ['idle', 'somnolent'],
  success: ['wink', 'fier'],
};
export const CAPSULE = SHAPE_BY_ID.get('capsule')!.radii;
export function mascotPose(state: MascotState, animation?: StateId, expression?: ExpressionId) {
  const [liveAnimation, liveExpression] = LIVE[state];
  return { animation: animation ?? liveAnimation, expression: expression ?? liveExpression };
}
export function createMascot(state: MascotState, animation?: StateId, expression?: ExpressionId) {
  const pose = mascotPose(state, animation, expression);
  return new BotEngine(100, pose.animation, CAPSULE, EXPRESSIONS.find((e) => e.id === pose.expression)!);
}
export function frozenTime(animation: StateId) { return POSES[animation]; }
export function cursorLook(x: number, y: number, box: { left: number; top: number; width: number; height: number }, viewport: { width: number; height: number }) {
  if (!box.width || !box.height || !Number.isFinite(x + y)) return null;
  const nx = Math.max(-1, Math.min(1, (x - box.left - box.width / 2) / Math.max(1, viewport.width / 2)));
  const ny = Math.max(-1, Math.min(1, (y - box.top - box.height / 2) / Math.max(1, viewport.height / 2)));
  return { yaw: nx * 16, pitch: 10 - ny * 13, mix: 1, spin: 0, wander: 0 };
}

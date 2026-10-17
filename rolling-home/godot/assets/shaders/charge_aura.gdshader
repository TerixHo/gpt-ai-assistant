shader_type spatial;
// 集氣光殼：邊緣發光（菲涅耳）、花紋繞著球旋轉；flame 為 1 時往上拉長成火焰。
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;

uniform vec4 glow_color : source_color = vec4(1.0, 0.82, 0.25, 1.0);
uniform vec4 core_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float intensity = 1.0;
uniform float spin = 1.0;
uniform float flame = 0.0;

float wave(vec2 p) {
	return sin(p.x) * 0.5 + 0.5;
}

void vertex() {
	float up = max(NORMAL.y, 0.0);
	float t = TIME * (6.0 + 10.0 * flame);
	float n = sin(VERTEX.x * 9.0 + t) * sin(VERTEX.z * 8.0 - t * 0.8) * 0.5 + 0.5;
	VERTEX += NORMAL * flame * (0.06 + 0.18 * n);
	VERTEX.y += flame * up * up * (0.35 + 0.55 * n);
}

void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.2);
	float angle = UV.x * 6.2831 * 6.0 - TIME * spin * 6.0;
	float bands = wave(vec2(angle + UV.y * 9.0, 0.0));
	float flick = 0.75 + 0.25 * sin(TIME * 23.0 + UV.y * 31.0);
	float glow = (fres * 1.2 + bands * 0.3 * (1.0 - fres) + 0.08) * flick;
	// 火焰：內側偏淺藍、外緣深藍
	vec3 col = mix(glow_color.rgb, core_color.rgb, clamp((1.0 - fres) * flame, 0.0, 1.0) * 0.55);
	ALBEDO = col * (1.0 + 0.35 * fres);
	ALPHA = clamp(glow * intensity, 0.0, 0.92);
}

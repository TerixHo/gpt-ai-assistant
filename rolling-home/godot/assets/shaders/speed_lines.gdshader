shader_type canvas_item;
// 衝刺時的速度線：從畫面中心往外放射、快速閃動的細線，中心留空。
// 白線與深色彩線交錯、邊緣一圈深色暗角，淺色地板或深色牆面上都看得到。

uniform float intensity : hint_range(0.0, 1.0) = 0.0;
uniform vec4 line_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 tint : source_color = vec4(0.55, 0.8, 1.0, 1.0);

float hash(float n) {
	return fract(sin(n * 12.9898) * 43758.5453);
}

void fragment() {
	vec2 res = 1.0 / SCREEN_PIXEL_SIZE;
	vec2 p = (UV - 0.5) * vec2(res.x / res.y, 1.0);
	float r = length(p);
	float a = atan(p.y, p.x) / 6.28318 + 0.5;
	float count = 120.0;
	float cell = floor(a * count);
	float frame = floor(TIME * 18.0);
	float on = step(0.62, hash(cell * 1.7 + frame * 3.1));
	float f = fract(a * count);
	float thin = smoothstep(0.42, 0.0, abs(f - 0.5));
	float start = 0.25 + 0.25 * hash(cell + frame);
	float radial = smoothstep(start, start + 0.25, r);
	float lines = on * thin * radial;
	float edge = smoothstep(0.38, 1.0, r) * 0.55;
	vec3 dark = tint.rgb * 0.35;
	vec3 lc = mix(tint.rgb * 0.5, line_color.rgb, step(0.45, hash(cell * 7.31 + frame)));
	vec3 col = mix(dark, lc, clamp(lines * 1.5, 0.0, 1.0));
	COLOR = vec4(col, clamp(max(lines * 0.95, edge), 0.0, 1.0) * intensity);
}

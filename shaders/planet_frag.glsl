#version 330

// Input vertex attributes (from vertex shader)
in vec3 fragPosition;
in vec4 fragColor;
in vec3 unrotatedNormal;
in vec3 fragNormal;

// Input uniform values
uniform sampler2D texture0;
uniform vec4 colDiffuse;

// Output fragment color
out vec4 finalColor;

// Input lighting values
uniform vec4 ambient;
uniform vec3 sunPos;
uniform vec3 viewPos;

uniform vec4 first_layer;
uniform vec4 second_layer;
uniform vec4 third_layer;
uniform vec4 fourth_layer;
uniform vec4 fifth_layer;

const float PI = 3.1415926535;

void main() {
    vec3 normal = normalize(unrotatedNormal);

	// Calculate UV coordinates from normal
	float u = atan(normal.x, normal.y)/(2*PI) + 0.5;
	float v = (asin(normal.z)/PI + 0.5);

    // Texel color fetching from texture sampler
    float noise = texture(texture0, vec2(u, v)).r;

    vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
    if (noise < 0.4) color.rgb = vec3(first_layer.r, first_layer.g, first_layer.b);
    else if (noise < 0.5) color.rgb = second_layer.rgb;
    else if (noise < 0.65) color.rgb = third_layer.rgb;
    else if (noise < 0.85) color.rgb = fourth_layer.rgb;
    else color.rgb = fifth_layer.rgb;

	// Calculate lighting normal from height map
	float fx0 = texture(texture0, vec2(u-0.01, v)).r, fx1 = texture(texture0, vec2(u+0.01, v)).r;
	float fy0 = texture(texture0, vec2(u, v-0.01)).r, fy1 = texture(texture0, vec2(u, v+0.01)).r;

	// the spacing of the grid in same units as the height map
	float eps = 1.0;

	// plug into the formulae above:
	normal = normalize(fragNormal);

	// create coordinate system
	vec3 nt = vec3(normal.z, 0.0, -normal.x) / length(normal.xz);
	vec3 nb = cross(normal, nt);

	vec3 bumpy_normal = normalize(vec3((fx0 - fx1)/(2.0*eps), 1.0, (fy0 - fy1)/(2.0*eps)));
	bumpy_normal = vec3(
		bumpy_normal.x * nb.x + bumpy_normal.y * normal.x + bumpy_normal.z * nt.x,
		bumpy_normal.x * nb.y + bumpy_normal.y * normal.y + bumpy_normal.z * nt.y,
		bumpy_normal.x * nb.z + bumpy_normal.y * normal.z + bumpy_normal.z * nt.z
	);

    vec3 viewD = normalize(viewPos - fragPosition);
	vec3 sunDir = normalize(sunPos - fragPosition);

    float lightDot = max(dot(bumpy_normal, sunDir), 0.0);

    float specular = 0.0;
	if (lightDot > 0.0) specular = pow(max(0.0, dot(viewD, reflect(-sunDir, bumpy_normal))), 16.0); // 16 is the alpha value in blinn-phong model

    finalColor = (color*((colDiffuse + vec4(specular, specular, specular, 1.0))*vec4(lightDot, lightDot, lightDot, 1.0)));
    finalColor += color*(ambient/10.0)*colDiffuse;

    // Gamma correction
    finalColor = pow(finalColor, vec4(1.0/2.2));
}

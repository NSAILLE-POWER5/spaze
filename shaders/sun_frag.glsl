#version 330

// Input vertex attributes (from vertex shader)
in vec4 fragColor;
in vec3 unrotatedNormal;

// Input uniform values
uniform sampler2D texture0;
uniform vec4 colDiffuse;

uniform float time;

// Output fragment color
out vec4 finalColor;

// Input lighting values
uniform vec3 viewPos;

const float PI = 3.1415926535;

void main() {
	vec3 normal = normalize(unrotatedNormal);

	// Calculate UV coordinates from normal
	float u = atan(normal.x, normal.y)/(2*PI) + 0.5;
	float v = asin(normal.z)/PI + 0.5;

    // Texel color fetching from texture sampler
    vec4 texelColor = texture(texture0, vec2(u, v))*fragColor;

	// TODO: Bloom/lens flare depending on view angle

	finalColor = texelColor * fragColor;

    // Gamma correction
    finalColor = pow(finalColor, vec4(1.0/2.2));
}

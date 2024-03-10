#version 330

// Input vertex attributes (from vertex shader)
in vec2 fragTexCoord;
in vec4 fragColor;

// Input uniform values
uniform sampler2D texture0;
uniform vec4 colDiffuse;

// Output fragment color
out vec4 finalColor;

const vec2 size = vec2(800, 800);
const float samples = 10.0;
const float quality = 2.0;

vec3 aces(vec3 x) {
	float a = 2.51f;
	float b = 0.03f;
	float c = 2.43f;
	float d = 0.59f;
	float e = 0.14f;
	return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}

void main() {
	vec4 sum = vec4(0);
    vec2 sizeFactor = vec2(1)/size*quality;

    // Texel color fetching from texture sampler
    vec4 source = texture2D(texture0, fragTexCoord);

    const int range = int((samples - 1)/2);            // should be = (samples - 1)/2;

	for (int x = -range; x <= range; x++) {
		for (int y = -range; y <= range; y++)
		{
			sum += texture2D(texture0, fragTexCoord + vec2(x, y)*sizeFactor);
		}
	}

    // Calculate final fragment color
	vec4 color = ((sum/(samples*samples)) + source)*colDiffuse;
    gl_FragColor = vec4(aces(color.xyz), color.a);
}

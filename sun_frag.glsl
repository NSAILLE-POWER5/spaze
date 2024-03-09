#version 330

// Input vertex attributes (from vertex shader)
in vec3 fragPosition;
in vec2 fragTexCoord;
//in vec4 fragColor;
in vec3 fragNormal;

// Input uniform values
uniform sampler2D texture0;
uniform vec4 colDiffuse;

// Output fragment color
out vec4 finalColor;

// Input lighting values
uniform vec3 viewPos;

void main() {
    // Texel color fetching from texture sampler
    vec4 texelColor = texture(texture0, fragTexCoord);

    vec3 normal = normalize(fragNormal);
	// TODO: Bloom/lens flare depending on view angle
    // vec3 viewD = normalize(viewPos - fragPosition);

	finalColor = texelColor * vec4(1.0, 0.8, 0.0, 1.0);

    // Gamma correction
    finalColor = pow(finalColor, vec4(1.0/2.2));
}

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
// uniform Light lights[MAX_LIGHTS];
uniform vec4 ambient;
uniform vec3 sunDir;
uniform vec3 viewPos;

void main() {
    // Texel color fetching from texture sampler
    vec4 texelColor = texture(texture0, fragTexCoord);

    vec3 normal = normalize(fragNormal);
    vec3 viewD = normalize(viewPos - fragPosition);

    float lightDot = max(dot(normal, sunDir), 0.0);

    float specular = 0.0;
	if (lightDot > 0.0) specular = pow(max(0.0, dot(viewD, reflect(-sunDir, normal))), 16.0); // 16 is the alpha value in blinn-phong model

    finalColor = (texelColor*((colDiffuse + vec4(specular, specular, specular, 1.0))*vec4(lightDot, lightDot, lightDot, 1.0)));
    finalColor += texelColor*(ambient/10.0)*colDiffuse;

    // Gamma correction
    finalColor = pow(finalColor, vec4(1.0/2.2));
}

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

const float PI = 3.1415926535;

void main() {
    vec3 normal = normalize(unrotatedNormal);

	// Calculate UV coordinates from normal
	float u = atan(normal.z, normal.x)/(2*PI) + 0.5;
	float v = asin(normal.y)/PI + 0.5;

    // Texel color fetching from texture sampler
    vec4 texelColor = texture(texture0, vec2(u, v)) * fragColor;

    normal = normalize(fragNormal);
    vec3 viewD = normalize(viewPos - fragPosition);
	vec3 sunDir = normalize(sunPos - fragPosition);

    float lightDot = max(dot(normal, sunDir), 0.0);

    float specular = 0.0;
	if (lightDot > 0.0) specular = pow(max(0.0, dot(viewD, reflect(-sunDir, normal))), 16.0); // 16 is the alpha value in blinn-phong model

    finalColor = (texelColor*((colDiffuse + vec4(specular, specular, specular, 1.0))*vec4(lightDot, lightDot, lightDot, 1.0)));
    finalColor += texelColor*(ambient/10.0)*colDiffuse;

    // Gamma correction
    finalColor = pow(finalColor, vec4(1.0/2.2));
}

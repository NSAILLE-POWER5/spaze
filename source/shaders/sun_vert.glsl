#version 330

// Input vertex attributes
in vec3 vertexPosition;
in vec3 vertexNormal;
in vec4 vertexColor;

// Input uniform values
uniform mat4 mvp;
uniform mat4 matNormal;

uniform float time;

// Output vertex attributes (to fragment shader)
out vec4 fragColor;
out vec3 unrotatedNormal;

void main()
{
    // Send vertex attributes to fragment shader
	vec3 pos = vertexPosition;
	pos += vertexNormal*sin(pos.x + pos.y*10.0 + time*0.5)*cos(pos.z)*0.02;

    fragColor = vertexColor;
	unrotatedNormal = vertexNormal;

    // Calculate final vertex position
    gl_Position = mvp*vec4(pos, 1.0);
}

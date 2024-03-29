#version 330

// Input vertex attributes
in vec2 vertexPosition;

// Fragment shader attributes
out vec2 fragPosition;

void main() {
	fragPosition = vertexPosition;

    // Calculate final vertex position
    gl_Position = vec4(vertexPosition, 0.0, 0.0);
}

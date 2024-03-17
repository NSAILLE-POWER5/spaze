#version 330

// Input vertex attributes
in vec3 vertexPosition;
in mat4 matModel;

// Input uniform values
uniform mat4 matProjection;
uniform mat4 matView;

void main()
{
    // Remove translation from the view matrix
    mat4 rotView = mat4(mat3(matView));
    vec4 clipPos = matProjection*rotView*matModel*vec4(vertexPosition, 1.0);

    // Calculate final vertex position
    gl_Position = clipPos;
}

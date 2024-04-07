#version 330

const float PI = 3.1415926535897932384626433832795;

// Input coordinate
in vec2 fragTexCoord;

// Output fragment color
out vec4 finalColor;

// How long since the effect started?
uniform float time;

float point(vec2 uv, float t, vec2 tp) {
    float slope = tp.y / tp.x;
    float dst_line = abs(slope*uv.x-uv.y)/sqrt(slope*slope + 1.0);
    
    vec2 dst = uv - tp;
    float a = dst.x*dst.x + dst.y*dst.y;
    a = 0.005*(t-0.05) / (a + dst_line);
    return max(a, 0.0);
}

vec3 get_col(vec2 uv, float a) {
    return 0.5 + 0.5*cos(time+uv.xyx+vec3(0,a*2.0,4));
}

void main() {
    vec2 uv = fragTexCoord*2.0 - 1.0;
    
    vec3 sum = vec3(0.0);
    
    for(float a = 0.0; a < 2.0*PI; a += PI/10.0) {
        vec3 col = get_col(uv, a);
        vec2 p = vec2(cos(a), sin(a));
        for (int i = 0; i < 3; i++) {
            float t = pow(time, 1.4)*1.3 + sqrt(time)*a/PI + float(i)/3.0 * 1.5  - PI;
            if (t > 0.0) {
                t = mod(t, 1.5);
                t = t*t;

                sum += col*point(uv, t, t*p);
            }
        }
    }
    
    // Output to screen
    finalColor = vec4(sum, 1.0);
}

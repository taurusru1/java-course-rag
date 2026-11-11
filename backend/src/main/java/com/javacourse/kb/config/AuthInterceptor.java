package com.javacourse.kb.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.javacourse.kb.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
@ConditionalOnBean(AuthService.class)
public class AuthInterceptor implements HandlerInterceptor {
    private final AuthService auth;
    private final ObjectMapper mapper;
    public AuthInterceptor(AuthService auth, ObjectMapper mapper) { this.auth = auth; this.mapper = mapper; }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if ("OPTIONS".equals(request.getMethod())) return true;
        String header = request.getHeader("Authorization");
        String token = header != null && header.startsWith("Bearer ") ? header.substring(7) : request.getParameter("access_token");
        try {
            request.setAttribute("authUser", auth.authenticate(token));
            return true;
        } catch (SecurityException error) {
            response.setStatus(401);
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
            response.setCharacterEncoding("UTF-8");
            mapper.writeValue(response.getWriter(), Map.of("code", 401, "message", error.getMessage()));
            return false;
        }
    }
}

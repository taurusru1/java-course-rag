package com.javacourse.kb.controller;

import com.javacourse.kb.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService auth;
    public AuthController(AuthService auth) { this.auth = auth; }

    public record LoginRequest(String account, String password, String role) {}

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody LoginRequest request) {
        if (request.account() == null || request.account().isBlank()) throw new IllegalArgumentException("请输入账号");
        if (request.password() == null || request.password().isBlank()) throw new IllegalArgumentException("请输入密码");
        return Map.of("code", 200, "data", auth.login(request.account(), request.password(), request.role()));
    }

    @GetMapping("/me")
    public Map<String, Object> me(HttpServletRequest request) {
        return Map.of("code", 200, "data", auth.currentUser(token(request)));
    }

    @PostMapping("/logout")
    public Map<String, Object> logout(HttpServletRequest request) {
        auth.logout(token(request));
        return Map.of("code", 200);
    }

    private String token(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        return header != null && header.startsWith("Bearer ") ? header.substring(7) : request.getParameter("access_token");
    }
}

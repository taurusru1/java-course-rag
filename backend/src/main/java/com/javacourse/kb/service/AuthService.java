package com.javacourse.kb.service;

import com.javacourse.kb.model.AuthSession;
import com.javacourse.kb.model.UserAccount;
import com.javacourse.kb.repository.AuthSessionRepository;
import com.javacourse.kb.repository.UserAccountRepository;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {
    private final UserAccountRepository users;
    private final AuthSessionRepository sessions;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public AuthService(UserAccountRepository users, AuthSessionRepository sessions) {
        this.users = users;
        this.sessions = sessions;
    }

    @Transactional
    public Map<String, Object> login(String account, String password, String role) {
        UserAccount user = users.findByAccountAndRole(
                account == null ? "" : account.trim(),
                role == null ? "" : role.trim()
            )
            .filter(UserAccount::isEnabled)
            .orElseThrow(() -> new IllegalArgumentException("账号或密码错误"));
        if (!encoder.matches(password == null ? "" : password, user.getPasswordHash())) {
            throw new IllegalArgumentException("账号或密码错误");
        }
        sessions.deleteByUserId(user.getId());
        AuthSession session = new AuthSession();
        session.setToken(UUID.randomUUID().toString().replace("-", ""));
        session.setUserId(user.getId());
        session.setExpiresAt(LocalDateTime.now().plusDays(7));
        sessions.save(session);
        return Map.of("token", session.getToken(), "user", userView(user));
    }

    public UserAccount authenticate(String token) {
        AuthSession session = sessions.findById(token == null ? "" : token)
            .filter(item -> item.getExpiresAt().isAfter(LocalDateTime.now()))
            .orElseThrow(() -> new SecurityException("登录状态已失效"));
        return users.findById(session.getUserId())
            .filter(UserAccount::isEnabled)
            .orElseThrow(() -> new SecurityException("账号不可用"));
    }

    public Map<String, Object> currentUser(String token) {
        return userView(authenticate(token));
    }

    @Transactional
    public void logout(String token) {
        if (token != null && !token.isBlank()) sessions.deleteById(token);
    }

    private Map<String, Object> userView(UserAccount user) {
        return Map.of(
            "id", user.getId(),
            "account", user.getAccount(),
            "role", user.getRole(),
            "displayName", user.getDisplayName(),
            "studentId", user.getStudentId() == null ? 0L : user.getStudentId()
        );
    }
}

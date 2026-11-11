package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "auth_sessions")
public class AuthSession {
    @Id @Column(length = 64)
    private String token;
    @Column(name = "user_id", nullable = false)
    private Long userId;
    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;
    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public LocalDateTime getExpiresAt() { return expiresAt; }
    public void setExpiresAt(LocalDateTime expiresAt) { this.expiresAt = expiresAt; }
}

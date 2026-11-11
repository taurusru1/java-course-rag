package com.javacourse.kb.repository;

import com.javacourse.kb.model.AuthSession;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuthSessionRepository extends JpaRepository<AuthSession, String> {
    void deleteByUserId(Long userId);
}

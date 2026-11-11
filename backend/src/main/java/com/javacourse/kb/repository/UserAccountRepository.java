package com.javacourse.kb.repository;

import com.javacourse.kb.model.UserAccount;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserAccountRepository extends JpaRepository<UserAccount, Long> {
    Optional<UserAccount> findByAccountAndRole(String account, String role);
}

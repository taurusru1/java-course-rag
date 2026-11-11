package com.javacourse.kb.config;

import com.javacourse.kb.model.UserAccount;
import com.javacourse.kb.repository.UserAccountRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 首次启动初始化演示账号（仅当 user_accounts 为空时执行），
 * 方便开发与答辩演示；生产环境应关闭或改为初始化脚本。
 */
@Component
public class DataSeeder implements CommandLineRunner {
    private static final Logger log = LoggerFactory.getLogger(DataSeeder.class);
    private final UserAccountRepository users;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public DataSeeder(UserAccountRepository users) { this.users = users; }

    @Override
    @Transactional
    public void run(String... args) {
        if (users.count() > 0) return;
        create("student", "123456", "STUDENT", "演示学生");
        create("teacher", "123456", "TEACHER", "课程教师");
        log.info("已初始化演示账号：student/123456（学生）、teacher/123456（教师）");
    }

    private void create(String account, String password, String role, String displayName) {
        UserAccount user = new UserAccount();
        user.setAccount(account);
        user.setPasswordHash(encoder.encode(password));
        user.setRole(role);
        user.setDisplayName(displayName);
        user.setEnabled(true);
        users.save(user);
    }
}

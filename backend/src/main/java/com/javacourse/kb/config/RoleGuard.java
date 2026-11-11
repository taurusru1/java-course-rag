package com.javacourse.kb.config;

import com.javacourse.kb.model.UserAccount;
import jakarta.servlet.http.HttpServletRequest;

/** 角色校验：写操作只允许教师。 */
public final class RoleGuard {

    private RoleGuard() {}

    public static UserAccount current(HttpServletRequest request) {
        Object user = request.getAttribute("authUser");
        if (user instanceof UserAccount account) return account;
        throw new SecurityException("未登录");
    }

    public static UserAccount requireTeacher(HttpServletRequest request) {
        UserAccount account = current(request);
        if (!"TEACHER".equalsIgnoreCase(account.getRole())) {
            throw new ForbiddenException("该操作需要教师权限");
        }
        return account;
    }
}

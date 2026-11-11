package com.javacourse.kb.config;

/** 已登录但角色不足（区别于未登录的 SecurityException）。 */
public class ForbiddenException extends RuntimeException {
    public ForbiddenException(String message) {
        super(message);
    }
}

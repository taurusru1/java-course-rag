package com.javacourse.kb.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.javacourse.kb.model.ErrorCase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/** 报错匹配打分测试：正则命中 0.9，关键词全中 0.7，未命中 0。 */
class DiagnoseServiceTest {
    private final DiagnoseService service = new DiagnoseService(null, null);

    private ErrorCase errorCase(String code, String pattern) {
        ErrorCase c = new ErrorCase();
        c.setErrorCode(code);
        c.setJavacPattern(pattern);
        return c;
    }

    @Test
    @DisplayName("正则命中返回 0.9")
    void regexHit() {
        ErrorCase c = errorCase("cannot_find_symbol", "cannot find symbol");
        assertEquals(0.9, service.score(c, "Hello.java:3: error: cannot find symbol"));
    }

    @Test
    @DisplayName("仅关键词命中返回 0.7")
    void keywordHit() {
        ErrorCase c = errorCase("null_pointer", "");
        assertEquals(0.7, service.score(c, "java.lang.NullPointerException: Cannot invoke"));
    }

    @Test
    @DisplayName("完全无关返回 0")
    void miss() {
        ErrorCase c = errorCase("array_index_out_of_bounds", "ArrayIndexOutOfBoundsException");
        assertEquals(0.0, service.score(c, "error: package org.springframework does not exist"));
    }

    @Test
    @DisplayName("非法正则不抛异常，降级为关键词匹配")
    void invalidRegexFallsBack() {
        ErrorCase c = errorCase("cannot_find_symbol", "([unclosed");
        assertEquals(0.7, service.score(c, "cannot find symbol"));
    }
}

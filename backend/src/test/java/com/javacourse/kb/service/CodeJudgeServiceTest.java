package com.javacourse.kb.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/** 代码题判分：真实编译 + 运行 + 输出比对。 */
class CodeJudgeServiceTest {
    private final CodeJudgeService service = new CodeJudgeService();

    @Test
    @DisplayName("输出正确时判为通过")
    void correctOutputPasses() {
        String source = """
            public class Sum {
                public static void main(String[] args) {
                    System.out.println(7 + 8);
                }
            }
            """;
        CodeJudgeService.Result result = service.judge(source, "15");
        assertTrue(result.compiled(), () -> "编译失败：" + result.compileError());
        assertTrue(result.passed());
        assertEquals("15", result.output());
    }

    @Test
    @DisplayName("输出不符时判错但不报编译错误")
    void wrongOutputFails() {
        CodeJudgeService.Result result = service.judge(
            "public class Sum { public static void main(String[] a) { System.out.println(1 + 2); } }", "15");
        assertTrue(result.compiled());
        assertFalse(result.passed());
        assertEquals("3", result.output());
    }

    @Test
    @DisplayName("编译失败时返回 javac 原文，供诊断使用")
    void compileErrorIsReturned() {
        CodeJudgeService.Result result = service.judge(
            "public class Broken { public static void main(String[] a) { int x = \"s\"; } }", "");
        assertFalse(result.compiled());
        assertFalse(result.passed());
        assertTrue(result.compileError().toLowerCase().contains("error"));
    }

    @Test
    @DisplayName("缺少分号能被识别为编译错误")
    void missingSemicolon() {
        CodeJudgeService.Result result = service.judge(
            "public class S { public static void main(String[] a) { int x = 1 System.out.println(x); } }", "");
        assertFalse(result.compiled());
        assertTrue(result.compileError().toLowerCase().contains("';'"));
    }

    @Test
    @DisplayName("从源码中识别类名，非 public 类也能运行")
    void detectClassName() {
        assertEquals("Foo", service.detectClassName("public class Foo { }"));
        assertEquals("Bar", service.detectClassName("class Bar { }"));
        assertEquals("Main", service.detectClassName("void main() { }"));
        CodeJudgeService.Result result = service.judge(
            "class Hello { public static void main(String[] a) { System.out.print(\"hi\"); } }", "hi");
        assertTrue(result.passed(), () -> result.compileError() + " / " + result.output());
    }

    @Test
    @DisplayName("空代码不调用编译器")
    void blankSource() {
        CodeJudgeService.Result result = service.judge("  ", "1");
        assertFalse(result.compiled());
        assertTrue(result.compileError().contains("代码为空"));
    }
}

package com.javacourse.kb.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 代码题判分：把学生提交的 Java 源码真正编译、运行，再和期望输出比对。
 *
 * <p>这是本系统「编程课程」属性的关键一环——客观题用文本比对够了，代码题不行：
 * 缩进、变量名、注释任何一处不同都会让字符串比对判错，学生写对了却得 0 分。
 * 因此这里用本机 javac 作为评判依据，顺带把编译错误原文交给
 * {@link DiagnoseService} 做诊断，形成「提交 → 编译 → 诊断 → 修复」的闭环。
 *
 * <p>安全边界：只允许一次编译 + 一次运行，各 10 秒超时；每次在独立临时目录执行，
 * 结束即删除。它不是完整的沙箱（没有禁网、没有限制内存），仅用于课程内演示，
 * 生产环境应换成容器化判题。
 */
@Service
public class CodeJudgeService {
    private static final Logger log = LoggerFactory.getLogger(CodeJudgeService.class);

    /** 编译超时（秒）。 */
    private static final long COMPILE_TIMEOUT_SECONDS = 10;
    /** 运行超时（秒）：防止学生写出死循环把判题线程拖死。 */
    private static final long RUN_TIMEOUT_SECONDS = 10;

    private static final Pattern PUBLIC_CLASS = Pattern.compile("public\\s+(?:final\\s+|abstract\\s+)?class\\s+(\\w+)");
    private static final Pattern ANY_CLASS = Pattern.compile("\\bclass\\s+(\\w+)");

    /**
     * 判题结果。
     *
     * @param compiled     是否编译通过
     * @param passed       是否判为正确（编译通过且输出符合期望）
     * @param compileError javac 原始报错（编译失败时）
     * @param output       程序运行的标准输出（编译成功时）
     * @param expected     期望输出
     * @param millis       耗时
     */
    public record Result(
        boolean compiled,
        boolean passed,
        String compileError,
        String output,
        String expected,
        long millis
    ) {
        public static Result compileFailure(String error, long millis) {
            return new Result(false, false, error, "", "", millis);
        }
    }

    public Result judge(String source, String expectedOutput) {
        long start = System.currentTimeMillis();
        if (source == null || source.isBlank()) {
            return Result.compileFailure("代码为空，请先编写 Java 源码。", 0);
        }
        String className = detectClassName(source);
        Path dir = null;
        try {
            dir = Files.createTempDirectory("javac-judge-");
            Path file = dir.resolve(className + ".java");
            Files.writeString(file, source, StandardCharsets.UTF_8);

            Exec compile = exec(dir, COMPILE_TIMEOUT_SECONDS,
                "javac", "-encoding", "UTF-8", "-d", dir.toString(),
                "-J-Duser.language=en", "-J-Duser.country=US", file.toString());
            if (compile.timedOut) {
                return Result.compileFailure("编译超时（超过 " + COMPILE_TIMEOUT_SECONDS + " 秒），请检查是否有死循环或超大文件。",
                    System.currentTimeMillis() - start);
            }
            if (compile.exitCode != 0) {
                return Result.compileFailure(compile.output.strip(), System.currentTimeMillis() - start);
            }

            Exec run = exec(dir, RUN_TIMEOUT_SECONDS, "java", "-cp", dir.toString(), className);
            if (run.timedOut) {
                return new Result(true, false, "", "运行超时（超过 " + RUN_TIMEOUT_SECONDS + " 秒），请检查循环条件。",
                    expectedOutput, System.currentTimeMillis() - start);
            }
            boolean emptyExpected = expectedOutput == null || expectedOutput.isBlank();
            boolean passed = emptyExpected ? run.exitCode == 0 : sameOutput(expectedOutput, run.output);
            return new Result(true, passed, "", run.output.strip(), expectedOutput, System.currentTimeMillis() - start);
        } catch (IOException e) {
            log.warn("判题环境不可用: {}", e.getMessage());
            return Result.compileFailure("判题环境不可用：" + e.getMessage(), System.currentTimeMillis() - start);
        } finally {
            deleteQuietly(dir);
        }
    }

    /** 期望输出与实际输出比对：忽略行尾空白与整体首尾空白，其余必须一致。 */
    boolean sameOutput(String expected, String actual) {
        return normalizeLines(expected).equals(normalizeLines(actual));
    }

    private String normalizeLines(String text) {
        if (text == null) return "";
        return text.replace("\r\n", "\n").replace('\r', '\n')
            .lines()
            .map(String::stripTrailing)
            .reduce((a, b) -> a + "\n" + b)
            .orElse("")
            .strip();
    }

    String detectClassName(String source) {
        Matcher pub = PUBLIC_CLASS.matcher(source);
        if (pub.find()) return pub.group(1);
        Matcher any = ANY_CLASS.matcher(source);
        if (any.find()) return any.group(1);
        return "Main";
    }

    private record Exec(int exitCode, String output, boolean timedOut) {}

    private Exec exec(Path workDir, long timeoutSeconds, String... command) throws IOException {
        ProcessBuilder builder = new ProcessBuilder(command).directory(workDir.toFile()).redirectErrorStream(true);
        Process process = builder.start();
        String output;
        try (var stream = process.getInputStream()) {
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            output = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
            if (!finished) {
                process.destroyForcibly();
                return new Exec(-1, output, true);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            process.destroyForcibly();
            return new Exec(-1, "", true);
        }
        return new Exec(process.exitValue(), output, false);
    }

    private void deleteQuietly(Path dir) {
        if (dir == null) return;
        try (Stream<Path> paths = Files.walk(dir)) {
            paths.sorted(Comparator.reverseOrder()).forEach(p -> {
                try {
                    Files.deleteIfExists(p);
                } catch (IOException ignored) {
                    // 临时目录清理失败不影响判题结果
                }
            });
        } catch (IOException ignored) {
            // 同上
        }
    }
}

package com.javacourse.kb.config;

import com.javacourse.kb.model.Chapter;
import com.javacourse.kb.model.Course;
import com.javacourse.kb.model.UserAccount;
import com.javacourse.kb.repository.ChapterRepository;
import com.javacourse.kb.repository.CourseRepository;
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
    private final CourseRepository courses;
    private final ChapterRepository chapters;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public DataSeeder(UserAccountRepository users, CourseRepository courses, ChapterRepository chapters) {
        this.users = users;
        this.courses = courses;
        this.chapters = chapters;
    }

    @Override
    @Transactional
    public void run(String... args) {
        if (users.count() == 0) {
            create("student", "123456", "STUDENT", "演示学生");
            create("teacher", "123456", "TEACHER", "课程教师");
            log.info("已初始化演示账号：student/123456（学生）、teacher/123456（教师）");
        }
        if (courses.count() == 0) seedDemoCourse();
    }

    /** 演示课程与章节：保证前端与检索链路有可用数据，正式数据由导入管道生成。 */
    private void seedDemoCourse() {
        Course course = new Course();
        course.setName("Java 程序设计");
        course.setCode("CS-JAVA-101");
        course.setDepartment("计算机学院");
        course.setSemester("2026 秋");
        course.setDescription("面向程序设计的 Java 入门课程，覆盖语法基础、面向对象、集合与异常处理。");
        Course saved = courses.save(course);
        String[][] rows = {
            {"1", "Java 基础语法", "变量与数据类型、运算符、流程控制、数组与方法。"},
            {"2", "面向对象编程", "类与对象、封装继承多态、接口与抽象类。"},
            {"3", "集合与异常", "List/Set/Map 常用实现、泛型、异常体系与 try-catch-finally。"}
        };
        for (String[] row : rows) {
            Chapter chapter = new Chapter();
            chapter.setCourseId(saved.getId());
            chapter.setChapterNo(Integer.parseInt(row[0]));
            chapter.setTitle(row[1]);
            chapter.setSummary(row[2]);
            chapters.save(chapter);
        }
        log.info("已初始化演示课程：{}（{} 章）", saved.getName(), rows.length);
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

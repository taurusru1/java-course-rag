package com.javacourse.kb.config;

import com.javacourse.kb.model.Chapter;
import com.javacourse.kb.model.Course;
import com.javacourse.kb.model.ErrorCase;
import com.javacourse.kb.model.KnowledgePoint;
import com.javacourse.kb.model.Question;
import com.javacourse.kb.model.UserAccount;
import com.javacourse.kb.repository.ChapterRepository;
import com.javacourse.kb.repository.CourseRepository;
import com.javacourse.kb.repository.ErrorCaseRepository;
import com.javacourse.kb.repository.KnowledgePointRepository;
import com.javacourse.kb.repository.QuestionRepository;
import com.javacourse.kb.repository.UserAccountRepository;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 首次启动初始化演示数据：账号、Java 课程与章节、知识点、示例题目、报错案例。
 * 仅在各表为空时执行；正式数据由导入管道与题库转换脚本生成。
 */
@Component
public class DataSeeder implements CommandLineRunner {
    private static final Logger log = LoggerFactory.getLogger(DataSeeder.class);
    private final UserAccountRepository users;
    private final CourseRepository courses;
    private final ChapterRepository chapters;
    private final KnowledgePointRepository points;
    private final QuestionRepository questions;
    private final ErrorCaseRepository errorCases;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public DataSeeder(UserAccountRepository users, CourseRepository courses, ChapterRepository chapters,
                      KnowledgePointRepository points, QuestionRepository questions, ErrorCaseRepository errorCases) {
        this.users = users;
        this.courses = courses;
        this.chapters = chapters;
        this.points = points;
        this.questions = questions;
        this.errorCases = errorCases;
    }

    @Override
    @Transactional
    public void run(String... args) {
        if (users.count() == 0) {
            createUser("student", "123456", "STUDENT", "演示学生");
            createUser("teacher", "123456", "TEACHER", "课程教师");
            log.info("已初始化演示账号：student/123456（学生）、teacher/123456（教师）");
        }
        Long courseId = courses.count() == 0 ? seedDemoCourse() : courses.findAll().get(0).getId();
        if (points.count() == 0) seedKnowledgePoints(courseId);
        if (questions.count() == 0) seedQuestions(courseId);
        if (errorCases.count() == 0) seedErrorCases();
    }

    /** 演示课程与章节：保证前端与检索链路有可用数据，正式数据由导入管道生成。 */
    private Long seedDemoCourse() {
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
        return saved.getId();
    }

    private void seedKnowledgePoints(Long courseId) {
        List<Chapter> list = chapters.findByCourseIdOrderByChapterNoAsc(courseId);
        long ch1 = list.get(0).getId(), ch2 = list.get(1).getId(), ch3 = list.get(2).getId();
        String[][] rows = {
            {"kp-java-var", "变量与数据类型", ch1 + "", "基本类型、引用类型、类型转换与字面量规则。", "2"},
            {"kp-java-flow", "流程控制", ch1 + "", "if/switch/for/while 与 break、continue 的语义。", "2"},
            {"kp-oop-class", "类与对象", ch2 + "", "类的定义、构造方法、封装与访问修饰符。", "3"},
            {"kp-oop-inherit", "继承与多态", ch2 + "", "extends、方法重写、向上转型与动态绑定。", "3"},
            {"kp-coll-list", "List 与 ArrayList", ch3 + "", "动态数组实现、扩容机制、随机访问与插入删除代价。", "3"},
            {"kp-exc-try", "异常处理", ch3 + "", "try-catch-finally、受检与非受检异常、自定义异常。", "3"}
        };
        for (String[] row : rows) {
            KnowledgePoint point = new KnowledgePoint();
            point.setCode(row[0]);
            point.setName(row[1]);
            point.setCourseId(courseId);
            point.setChapterId(Long.parseLong(row[2]));
            point.setDescription(row[3]);
            point.setDifficulty(Integer.parseInt(row[4]));
            points.save(point);
        }
        log.info("已初始化 {} 个知识点", rows.length);
    }

    private void seedQuestions(Long courseId) {
        List<KnowledgePoint> list = points.findByCourseIdOrderByIdAsc(courseId);
        List<Chapter> chapterList = chapters.findByCourseIdOrderByChapterNoAsc(courseId);
        String[][][] rows = {
            {{"CHOICE", "下列哪个是合法的 Java 标识符？",
              "[\"A. 2name\",\"B. _name\",\"C. class\",\"D. my-name\"]", "B",
              "标识符不能以数字开头（排除 A），不能是关键字（排除 C），不能包含连字符（排除 D）。"},
             {"CHOICE", "下列哪个访问修饰符表示“仅本类可见”？",
              "[\"A. public\",\"B. protected\",\"C. private\",\"D. default（包可见）\"]", "C",
              "private 限定在类内部；default 是包级可见；protected 允许子类访问；public 全局可见。"}},
            {{"JUDGE", "在 Java 中，char 类型占用 2 个字节。", "[\"T. 正确\",\"F. 错误\"]", "T",
              "Java 使用 Unicode，char 为 16 位无符号整数，占 2 个字节。"},
             {"FILL", "在 switch 语句中，用于跳出当前分支的关键字是 ______。", null, "break",
              "break 结束 switch；若省略会发生穿透（fall-through），可用 return 或新式 switch 表达式替代。"}},
            {{"CHOICE", "ArrayList 的底层数据结构是？",
              "[\"A. 双向链表\",\"B. 动态数组\",\"C. 红黑树\",\"D. 哈希表\"]", "B",
              "ArrayList 基于 Object[]，扩容约 1.5 倍；随机访问 O(1)，中间插入删除 O(n)。"},
             {"FILL", "捕获异常使用的关键字是 ______。", null, "catch",
              "try 包裹可能异常的代码，catch 捕获并处理，finally 负责资源清理。"}}
        };
        String[] pointCodes = {"kp-java-var", "kp-oop-class", "kp-coll-list"};
        int count = 0;
        for (int i = 0; i < rows.length; i++) {
            KnowledgePoint point = points.findByCode(pointCodes[i]).orElse(null);
            for (String[] row : rows[i]) {
                Question question = new Question();
                question.setCourseId(courseId);
                question.setChapterId(chapterList.get(i).getId());
                question.setKnowledgePointId(point == null ? null : point.getId());
                question.setType(row[0]);
                question.setStem(row[1]);
                question.setOptionsJson(row[2]);
                question.setAnswer(row[3]);
                question.setAnalysis(row[4]);
                question.setDifficulty(2);
                question.setSource("自建示例题库");
                questions.save(question);
                count++;
            }
        }
        log.info("已初始化 {} 道示例题目", count);
    }

    private void seedErrorCases() {
        String[][] rows = {
            {"cannot_find_symbol", "编译错误", "(cannot find symbol|找不到符号)",
             "编译器在当前作用域找不到该标识符：可能拼写错误、变量未声明、缺少 import 或作用域越界。",
             "1) 检查拼写与大小写；2) 确认变量/方法已声明且在作用域内；3) 使用类时补充 import；4) 检查前一行是否缺少分号导致解析错位。",
             "System.out.println(name); // name 未声明"},
            {"incompatible_types", "编译错误", "(incompatible types|不兼容的类型)",
             "赋值或传参时类型不匹配，例如把 String 赋给 int，或把 double 直接赋给 int。",
             "1) 核对左右两侧类型；2) 需要时显式转型 (int) d；3) 字符串转数字用 Integer.parseInt；4) 泛型集合注意元素类型。",
             "int count = \"10\"; // 应为 Integer.parseInt(\"10\")"},
            {"missing_return_statement", "编译错误", "(missing return statement|缺少返回语句)",
             "有返回值的方法存在未覆盖的分支，编译器无法确认所有路径都返回。",
             "1) 所有 if/switch 分支都 return；2) 循环后补兜底 return；3) 确认方法签名返回类型是否写错。",
             "int max(int a, int b) { if (a > b) return a; }"},
            {"null_pointer", "运行时异常", "(NullPointerException|空指针)",
             "对 null 引用调用方法或访问字段。",
             "1) 调用前判空；2) 用 Objects.requireNonNull 明确约束；3) 检查 Map.get / List.get 返回 null 的情况；4) 用 Optional 表达缺失值。",
             "String s = null; s.length();"},
            {"array_index_out_of_bounds", "运行时异常", "(ArrayIndexOutOfBoundsException|IndexOutOfBoundsException|数组越界)",
             "下标超出 0..length-1 范围（常见差一错误）。",
             "1) 循环条件用 i < arr.length；2) 检查 list.get(size) 这类差一错误；3) 打印下标与长度定位。",
             "int[] a = new int[3]; a[3] = 1;"}
        };
        for (String[] row : rows) {
            ErrorCase errorCase = new ErrorCase();
            errorCase.setErrorCode(row[0]);
            errorCase.setCategory(row[1]);
            errorCase.setJavacPattern(row[2]);
            errorCase.setCause(row[3]);
            errorCase.setSolution(row[4]);
            errorCase.setExampleCode(row[5]);
            errorCases.save(errorCase);
        }
        log.info("已初始化 {} 条报错案例", rows.length);
    }

    private void createUser(String account, String password, String role, String displayName) {
        UserAccount user = new UserAccount();
        user.setAccount(account);
        user.setPasswordHash(encoder.encode(password));
        user.setRole(role);
        user.setDisplayName(displayName);
        user.setEnabled(true);
        users.save(user);
    }
}

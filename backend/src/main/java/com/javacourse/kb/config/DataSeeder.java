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
            {"kp-oop-inherit", "继承与重写", ch2 + "", "extends、方法重写、super 与构造顺序。", "3"},
            {"kp-oop-poly", "接口与多态", ch2 + "", "接口与抽象类的差别、向上转型与动态绑定。", "3"},
            {"kp-coll-list", "List 与 ArrayList", ch3 + "", "动态数组实现、扩容机制、随机访问与插入删除代价。", "3"},
            {"kp-coll-map", "Map 与 HashMap", ch3 + "", "哈希表结构、hashCode 与 equals 约定、扩容与树化。", "3"},
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
        List<Chapter> chapterList = chapters.findByCourseIdOrderByChapterNoAsc(courseId);
        // 列：章节下标、知识点编码、题型、题干、选项 JSON、标准答案、解析
        String[][] rows = {
            {"0", "kp-java-var", "CHOICE", "下列哪个是合法的 Java 标识符？",
             "[\"A. 2name\",\"B. _name\",\"C. class\",\"D. my-name\"]", "B",
             "标识符不能以数字开头（排除 A），不能是关键字（排除 C），不能包含连字符（排除 D）。"},
            {"0", "kp-java-var", "CHOICE", "下列哪个不是 Java 的基本数据类型？",
             "[\"A. int\",\"B. String\",\"C. boolean\",\"D. char\"]", "B",
             "基本类型共 8 种：byte/short/int/long/float/double/char/boolean；String 是引用类型。"},
            {"0", "kp-java-var", "JUDGE", "在 Java 中，char 类型占用 2 个字节。", "[\"T. 正确\",\"F. 错误\"]", "T",
             "Java 使用 Unicode，char 为 16 位无符号整数，占 2 个字节。"},
            {"0", "kp-java-flow", "FILL", "在 switch 语句中，用于跳出当前分支的关键字是 ______。", null, "break",
             "break 结束 switch；若省略会发生穿透（fall-through），可用 return 或新式 switch 表达式替代。"},
            {"0", "kp-java-flow", "CHOICE", "for 循环中 continue 的作用是？",
             "[\"A. 结束整个循环\",\"B. 跳过本次迭代，进入下一次\",\"C. 跳出方法\",\"D. 重新开始循环\"]", "B",
             "continue 只跳过当前轮剩余语句；break 才结束整个循环；return 结束方法。"},
            {"0", "kp-java-var", "FILL", "获取数组长度使用的属性名是 ______。", null, "length",
             "数组用 arr.length（属性，无括号）；字符串用 s.length()（方法）；集合用 list.size()。"},
            {"1", "kp-oop-class", "CHOICE", "下列哪个访问修饰符表示“仅本类可见”？",
             "[\"A. public\",\"B. protected\",\"C. private\",\"D. default（包可见）\"]", "C",
             "private 限定在类内部；default 是包级可见；protected 允许子类访问；public 全局可见。"},
            {"1", "kp-oop-class", "JUDGE", "在 Java 中，一个类可以同时继承多个父类。", "[\"T. 正确\",\"F. 错误\"]", "F",
             "Java 是单继承，一个类只能 extends 一个类，但可以实现多个接口。"},
            {"1", "kp-oop-inherit", "FILL", "子类构造器中调用父类构造器使用的关键字是 ______。", null, "super",
             "super(...) 必须位于子类构造器第一行；省略时编译器会插入无参的 super()。"},
            {"1", "kp-oop-poly", "CHOICE", "父类引用指向子类对象，调用被重写的方法时执行的是？",
             "[\"A. 父类的方法\",\"B. 子类的方法\",\"C. 编译报错\",\"D. 取决于是否加 final\"]", "B",
             "多态依赖动态绑定：运行时按对象的实际类型选择方法实现。"},
            {"1", "kp-oop-poly", "JUDGE", "接口中声明的字段默认是 public static final 的。", "[\"T. 正确\",\"F. 错误\"]", "T",
             "接口字段隐式为 public static final，必须初始化；方法隐式为 public abstract（默认方法除外）。"},
            {"1", "kp-oop-class", "CHOICE", "在 static 方法中，不能直接使用的是？",
             "[\"A. 静态字段\",\"B. 静态方法\",\"C. 本类的实例字段与 this\",\"D. 局部变量\"]", "C",
             "static 方法属于类，没有隐式 this，因此不能直接访问实例成员。"},
            {"2", "kp-coll-list", "CHOICE", "ArrayList 的底层数据结构是？",
             "[\"A. 双向链表\",\"B. 动态数组\",\"C. 红黑树\",\"D. 哈希表\"]", "B",
             "ArrayList 基于 Object[]，扩容约 1.5 倍；随机访问 O(1)，中间插入删除 O(n)。"},
            {"2", "kp-coll-map", "CHOICE", "把对象作为 HashMap 的键时，必须重写哪两个方法？",
             "[\"A. toString 与 clone\",\"B. hashCode 与 equals\",\"C. compareTo 与 sort\",\"D. finalize 与 getClass\"]", "B",
             "先按 hashCode 定位桶，再用 equals 判断键相等；两者不一致会导致 get 取不到已 put 的值。"},
            {"2", "kp-coll-map", "JUDGE", "在 Java 中可以直接声明 List<int> 这样的泛型集合。", "[\"T. 正确\",\"F. 错误\"]", "F",
             "泛型参数必须是引用类型，应写 List<Integer>；基本类型由自动装箱转换。"},
            {"2", "kp-coll-list", "CHOICE", "用 for-each 遍历 ArrayList 的同时调用 list.remove 会抛出？",
             "[\"A. NullPointerException\",\"B. ClassCastException\",\"C. ConcurrentModificationException\",\"D. 不抛异常\"]", "C",
             "迭代器检测到结构性修改会快速失败；应改用 Iterator.remove 或 removeIf。"},
            {"2", "kp-exc-try", "FILL", "捕获异常使用的关键字是 ______。", null, "catch",
             "try 包裹可能异常的代码，catch 捕获并处理，finally 负责资源清理。"},
            {"2", "kp-exc-try", "FILL", "try-with-resources 结束时自动调用资源的 ______ 方法。", null, "close",
             "资源需实现 AutoCloseable，退出 try 块时按声明的逆序自动调用 close()。"}
        };
        int count = 0;
        for (String[] row : rows) {
            KnowledgePoint point = points.findByCode(row[1]).orElse(null);
            Question question = new Question();
            question.setCourseId(courseId);
            question.setChapterId(chapterList.get(Integer.parseInt(row[0])).getId());
            question.setKnowledgePointId(point == null ? null : point.getId());
            question.setType(row[2]);
            question.setStem(row[3]);
            question.setOptionsJson(row[4]);
            question.setAnswer(row[5]);
            question.setAnalysis(row[6]);
            question.setDifficulty(2);
            question.setSource("自建示例题库");
            questions.save(question);
            count++;
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

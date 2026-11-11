# 第 1 章 Java 基础语法

## 1.1 标识符与关键字

Java 的标识符由字母、数字、下划线 `_` 和美元符号 `$` 组成，首字符不能是数字，也不能使用关键字（如 `class`、`int`、`for`）。类名采用大驼峰，方法与变量采用小驼峰，常量全大写并用下划线分隔。

常见错误是使用数字开头或连字符命名，例如 `2name` 与 `my-name` 都会导致编译失败。

## 1.2 基本数据类型

Java 有 8 种基本数据类型：`byte`、`short`、`int`、`long`、`float`、`double`、`char`、`boolean`。整数字面量默认是 `int`，小数默认是 `double`；需要 `long` 时加 `L` 后缀，需要 `float` 时加 `F` 后缀。

```java
public class NumberDemo {
    public static void main(String[] args) {
        int count = 10;
        long total = 1024L;
        double ratio = 0.75;
        float rate = 0.5F;
        char grade = 'A';
        boolean passed = true;
        System.out.println(count + total + ratio + rate + grade + passed);
    }
}
```

基本类型之间的转换分为自动类型提升与强制类型转换。`int` 转 `double` 是安全的自动提升，`double` 转 `int` 会截断小数部分，必须显式强转。

## 1.3 流程控制

`if-else` 用于分支，`switch` 用于多路等值判断。JDK 14 之后 `switch` 支持箭头语法，可以返回值，不需要显式 `break`。

```java
public class GradeDemo {
    public static String level(int score) {
        if (score >= 90) {
            return "A";
        } else if (score >= 60) {
            return "B";
        }
        return "C";
    }

    public static String levelWithSwitch(int score) {
        return switch (score / 10) {
            case 9, 10 -> "A";
            case 6, 7, 8 -> "B";
            default -> "C";
        };
    }
}
```

循环包括 `for`、`while`、`do-while` 与增强 `for`。`break` 结束整个循环，`continue` 跳过本次迭代。注意 `switch` 的每个 `case` 在旧语法中需要 `break`，否则会发生穿透。

## 1.4 数组

数组是定长容器，使用 `new` 创建后长度不可变。`int[] values = new int[5];` 会得到全 0 的数组；`String[] names` 默认元素为 `null`，直接调用方法会抛出 `NullPointerException`。

```java
public class ArrayDemo {
    public static void main(String[] args) {
        int[] values = new int[5];
        for (int i = 0; i < values.length; i++) {
            values[i] = i * i;
        }
        int sum = 0;
        for (int value : values) {
            sum += value;
        }
        System.out.println("sum = " + sum);
    }
}
```

数组下标从 0 开始，访问 `values[5]` 会抛出 `ArrayIndexOutOfBoundsException`。

## 1.5 方法与方法重载

方法签名由方法名与参数列表共同决定，返回值类型不参与重载。参数传递是值传递：基本类型传值，引用类型传引用的副本。

```java
public class MethodDemo {
    public static int max(int a, int b) {
        return a > b ? a : b;
    }

    public static double max(double a, double b) {
        return a > b ? a : b;
    }

    public static int max(int a, int b, int c) {
        return max(max(a, b), c);
    }

    public static void main(String[] args) {
        System.out.println(max(3, 5));
        System.out.println(max(3.5, 2.5));
        System.out.println(max(1, 9, 4));
    }
}
```

调用 `max` 时编译器按实参类型选择最匹配的重载版本，这一过程称为重载解析。

## 1.6 面向对象入门

类由字段与方法组成，`new` 在堆上创建对象，构造器负责初始化。`this` 指向当前对象，`static` 成员属于类而不是实例。

```java
public class Student {
    private final String name;
    private int score;

    public Student(String name) {
        this.name = name;
        this.score = 0;
    }

    public void addScore(int delta) {
        if (delta <= 0) {
            throw new IllegalArgumentException("delta 必须为正数");
        }
        this.score += delta;
    }

    public boolean isPassed() {
        return this.score >= 60;
    }

    public String getName() {
        return name;
    }

    @Override
    public String toString() {
        return "Student{" + name + ", score=" + score + "}";
    }
}
```

## 1.7 常见编译错误

初学者最常见的三条编译错误：

1. `cannot find symbol`：变量、方法或类名拼写错误，或忘记 `import`。
2. `incompatible types`：把 `double` 直接赋给 `int` 却没有强转。
3. `missing return statement`：声明了返回值的方法在所有分支上都必须返回。

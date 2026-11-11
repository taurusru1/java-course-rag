# 第 2 章 面向对象

## 2.1 类与对象

类是对一类事物的抽象，包含字段（状态）和方法（行为）。对象是类的实例，通过 `new` 在堆上创建，引用变量存放在栈上。构造器与类同名且没有返回值类型，负责给字段赋初值；如果一个构造器都没写，编译器会补一个无参构造器，一旦写了带参构造器，无参构造器就不再自动生成。

```java
public class Account {
    private String owner;
    private double balance;

    public Account(String owner, double balance) {
        this.owner = owner;
        this.balance = balance;
    }

    public void deposit(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("金额必须为正数");
        }
        this.balance += amount;
    }

    public double getBalance() {
        return balance;
    }
}
```

调用 `new Account("张三", 100)` 时，先分配对象内存并把字段置为默认值（`0`、`0.0`、`false`、`null`），再执行构造器体完成赋值。

## 2.2 封装与访问控制

封装是把字段设为 `private`，只通过公开方法访问，从而在方法内部校验数据合法性。访问修饰符的作用范围从大到小为 `public`、`protected`、默认（包内可见）、`private`，成员变量优先使用最小可见性。

```java
public class Score {
    private int value;

    public void setValue(int value) {
        if (value < 0 || value > 100) {
            throw new IllegalArgumentException("分数必须在 0 到 100 之间");
        }
        this.value = value;
    }

    public int getValue() {
        return value;
    }
}
```

如果把 `value` 声明为 `public`，外部可以直接写入 `-5`，校验逻辑就被绕过了，这正是封装要解决的问题。

## 2.3 继承与方法重写

子类用 `extends` 继承父类，获得父类非私有成员。方法重写要求方法名、参数列表相同，返回值类型兼容，访问权限不能更严格；建议加 `@Override` 让编译器检查签名是否真的重写成功。创建子类对象时，构造顺序是父类字段初始化、父类构造器、子类字段初始化、子类构造器。

```java
public class Animal {
    protected String name;

    public Animal(String name) {
        this.name = name;
    }

    public String sound() {
        return "...";
    }
}

public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public String sound() {
        return "汪汪";
    }
}
```

## 2.4 多态与向上转型

父类引用指向子类对象称为向上转型，调用被重写的方法时执行的是子类版本，这一机制称为动态绑定。多态让调用方依赖抽象而不是具体实现，新增子类时无需修改调用代码。

```java
public class Zoo {
    public static void main(String[] args) {
        Animal[] animals = { new Dog("旺财"), new Cat("咪咪") };
        for (Animal animal : animals) {
            System.out.println(animal.name + ": " + animal.sound());
        }
    }
}
```

向上转型后只能调用父类声明的方法；需要调用子类特有方法时必须向下转型，并用 `instanceof` 判断，否则可能抛出 `ClassCastException`。

## 2.5 抽象类与接口

抽象类用 `abstract` 声明，可以有字段、构造器和已实现方法，但不能被实例化，适合表达「是什么」。接口用 `interface` 声明，方法默认是 `public abstract`，字段默认是 `public static final`，适合表达「能做什么」，一个类可以实现多个接口。

```java
public interface Payable {
    double pay();
}

public abstract class Employee implements Payable {
    protected final String name;

    protected Employee(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    @Override
    public abstract double pay();
}
```

JDK 8 之后接口可以写 `default` 方法与 `static` 方法，用于在不破坏实现类的前提下扩展接口。

## 2.6 static 与 final

`static` 成员属于类而不是实例，所有对象共享一份，通过类名访问；`static` 方法里不能使用 `this` 和 `super`，也不能直接访问实例字段。`final` 修饰变量表示只能赋值一次，修饰方法表示不能重写，修饰类表示不能被继承。

```java
public class Counter {
    private static int total = 0;
    private final int id;

    public Counter(int id) {
        this.id = id;
        total++;
    }

    public static int getTotal() {
        return total;
    }
}
```

`static` 变量在类加载时初始化，常用来做计数器或常量表；把可变状态放进 `static` 字段会带来线程安全问题。

## 2.7 常见错误

1. 在 `static` 方法中写 `this.name`，编译报 `non-static variable this cannot be referenced from a static context`。
2. 重写时参数列表写错（例如父类是 `int`，子类写成 `Integer`），变成重载而不是重写，加 `@Override` 可提前发现。
3. 子类构造器没有显式调用 `super(...)`，而父类又没有无参构造器，编译报 `constructor ... cannot be applied to given types`。
4. 对 `null` 引用调用方法，运行时抛 `NullPointerException`；对象创建后未判空是初学阶段最高频的运行时异常。

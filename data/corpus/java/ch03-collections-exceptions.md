# 第 3 章 集合与异常

## 3.1 集合体系

Java 集合分两大接口：`Collection`（单列）与 `Map`（键值对）。`Collection` 下又分 `List`（有序可重复）、`Set`（不可重复）、`Queue`（队列）。`ArrayList`、`LinkedList`、`HashSet`、`HashMap` 是最常用的四个实现类，选择依据是查找、插入、删除的复杂度以及是否需要有序。

```java
import java.util.ArrayList;
import java.util.List;

public class ListDemo {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>();
        names.add("张三");
        names.add("李四");
        names.add("张三");
        System.out.println(names.size());
        System.out.println(names.get(1));
    }
}
```

`List` 允许重复元素并且按插入顺序保存，`size()` 返回元素个数，`get(i)` 按下标访问。

## 3.2 ArrayList 与 LinkedList

`ArrayList` 底层是数组，随机访问是 O(1)，中间插入删除需要搬移元素；`LinkedList` 底层是双向链表，头尾插入删除是 O(1)，随机访问要遍历。绝大多数业务场景选 `ArrayList`，只有频繁在两端增删时才考虑 `LinkedList`。

```java
import java.util.ArrayList;
import java.util.List;

public class GrowDemo {
    public static void main(String[] args) {
        List<Integer> values = new ArrayList<>(2);
        for (int i = 0; i < 10; i++) {
            values.add(i);
        }
        System.out.println(values.size());
    }
}
```

`ArrayList` 容量不足时按约 1.5 倍扩容并复制数组，因此已知数据量时应在构造器里指定初始容量，减少扩容次数。

## 3.3 HashMap 原理

`HashMap` 用数组加链表（JDK 8 起链表长度超过 8 且容量不小于 64 时转为红黑树）存储键值对。插入时先对 `key` 调用 `hashCode()` 再扰动得到数组下标，冲突时挂在同一桶的链表上；查找时先比哈希再比 `equals`，因此自定义对象作为键时必须同时正确重写 `hashCode` 与 `equals`。

```java
import java.util.HashMap;
import java.util.Map;

public class MapDemo {
    public static void main(String[] args) {
        Map<String, Integer> scores = new HashMap<>();
        scores.put("张三", 90);
        scores.put("李四", 85);
        scores.put("张三", 95);
        System.out.println(scores.get("张三"));
        System.out.println(scores.getOrDefault("王五", 0));
    }
}
```

`put` 相同的键会覆盖旧值并返回旧值，`get` 不存在的键返回 `null`，所以取值时更推荐 `getOrDefault`。`HashMap` 不保证顺序，需要按插入顺序遍历时用 `LinkedHashMap`，需要按键排序时用 `TreeMap`。

## 3.4 泛型

泛型在编译期提供类型检查，避免强制类型转换。`List<String>` 只能放字符串，取出时不需要强转；`List` 不加泛型（原始类型）则什么都能放，取出时容易抛 `ClassCastException`。泛型参数不能是基本类型，`List<int>` 非法，应写 `List<Integer>`。

```java
import java.util.ArrayList;
import java.util.List;

public class GenericDemo {
    public static <T> T first(List<T> items) {
        return items.isEmpty() ? null : items.get(0);
    }

    public static void main(String[] args) {
        List<String> names = new ArrayList<>();
        names.add("张三");
        String name = first(names);
        System.out.println(name);
    }
}
```

泛型在编译后会被擦除，运行时无法通过 `instanceof List<String>` 判断类型参数。

## 3.5 异常体系

`Throwable` 下分 `Error` 与 `Exception`，`Exception` 又分受检异常（`IOException`、`SQLException`，必须捕获或声明抛出）与非受检异常（`RuntimeException` 及其子类，如 `NullPointerException`、`ArrayIndexOutOfBoundsException`、`IllegalArgumentException`）。捕获时子类异常要写在父类异常前面，否则编译报错。

```java
public class Divider {
    public static int divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("除数不能为 0");
        }
        return a / b;
    }

    public static void main(String[] args) {
        try {
            System.out.println(divide(10, 0));
        } catch (IllegalArgumentException e) {
            System.out.println("参数错误：" + e.getMessage());
        } finally {
            System.out.println("结束");
        }
    }
}
```

`finally` 无论是否发生异常都会执行，常用于释放资源；`try` 块中如果有 `return`，`finally` 仍会先执行。

## 3.6 try-with-resources 与自定义异常

实现了 `AutoCloseable` 的资源可以写在 `try` 的括号里，离开代码块时自动调用 `close()`，即使抛出异常也会关闭，不需要手写 `finally`。

```java
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class ReadDemo {
    public static String firstLine(String path) throws IOException {
        try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
            return reader.readLine();
        }
    }
}
```

自定义异常通常继承 `RuntimeException`（非受检）或 `Exception`（受检），并提供带 `message` 和 `cause` 的构造器，抛出时保留原始异常便于定位问题。

## 3.7 常见错误

1. 遍历集合时调用 `list.remove(...)`，抛出 `ConcurrentModificationException`，应使用 `Iterator.remove()` 或 `removeIf`。
2. 从 `List` 取出元素时强转类型不匹配，抛出 `ClassCastException`，根源是使用了原始类型集合。
3. 数组下标越界，抛出 `ArrayIndexOutOfBoundsException`，循环条件应写 `i < array.length`。
4. 捕获异常后只写 `e.printStackTrace()` 而不处理，或直接 `catch (Exception e) {}` 吞掉异常，导致问题难以定位。

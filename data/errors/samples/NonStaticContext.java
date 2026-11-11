public class NonStaticContext {
    private int count = 0;
    public static void main(String[] args) {
        count++;
        System.out.println(count);
    }
}
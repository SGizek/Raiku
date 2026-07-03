package dev.raiku.javastream;

import java.util.*;
import java.util.function.BiFunction;
import java.util.stream.IntStream;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

/**
 * StreamUtils — Extended Java Stream combinators.
 *
 * <p>All methods return new streams and do not consume their input streams
 * eagerly.
 */
public final class StreamUtils {

    private StreamUtils() {}

    // -----------------------------------------------------------------------
    // zip
    // -----------------------------------------------------------------------

    /**
     * Zip two streams element-by-element using {@code combiner}, stopping
     * at the shorter stream.
     *
     * <pre>{@code
     * var names = Stream.of("Alice", "Bob");
     * var scores = Stream.of(95, 87);
     * StreamUtils.zip(names, scores, (n, s) -> n + "=" + s)
     *            .forEach(System.out::println);
     * // Alice=95
     * // Bob=87
     * }</pre>
     */
    public static <A, B, C> Stream<C> zip(
            Stream<A> a,
            Stream<B> b,
            BiFunction<A, B, C> combiner
    ) {
        final Iterator<A> iterA = a.iterator();
        final Iterator<B> iterB = b.iterator();

        final Iterator<C> combined = new Iterator<>() {
            @Override public boolean hasNext() {
                return iterA.hasNext() && iterB.hasNext();
            }
            @Override public C next() {
                return combiner.apply(iterA.next(), iterB.next());
            }
        };

        final Spliterator<C> spliterator = Spliterators.spliteratorUnknownSize(
                combined, Spliterator.ORDERED);
        return StreamSupport.stream(spliterator, false);
    }

    // -----------------------------------------------------------------------
    // windowed
    // -----------------------------------------------------------------------

    /**
     * Return a stream of overlapping windows of size {@code n} over {@code source}.
     * Each window is a new {@link List} containing exactly {@code n} elements.
     *
     * <pre>{@code
     * StreamUtils.windowed(Stream.of(1,2,3,4,5), 3)
     *            .forEach(System.out::println);
     * // [1, 2, 3]
     * // [2, 3, 4]
     * // [3, 4, 5]
     * }</pre>
     */
    public static <T> Stream<List<T>> windowed(Stream<T> source, int n) {
        if (n <= 0) throw new IllegalArgumentException("Window size must be > 0");
        final List<T> buffer = new ArrayList<>(source.toList());
        return IntStream.rangeClosed(0, buffer.size() - n)
                .mapToObj(i -> Collections.unmodifiableList(buffer.subList(i, i + n)));
    }

    // -----------------------------------------------------------------------
    // chunk
    // -----------------------------------------------------------------------

    /**
     * Partition {@code source} into non-overlapping chunks of size {@code n}.
     * The last chunk may be smaller if the stream length is not divisible by n.
     *
     * <pre>{@code
     * StreamUtils.chunk(Stream.of(1,2,3,4,5), 2)
     *            .forEach(System.out::println);
     * // [1, 2]
     * // [3, 4]
     * // [5]
     * }</pre>
     */
    public static <T> Stream<List<T>> chunk(Stream<T> source, int n) {
        if (n <= 0) throw new IllegalArgumentException("Chunk size must be > 0");
        final List<T> all = source.toList();
        return IntStream.iterate(0, i -> i < all.size(), i -> i + n)
                .mapToObj(i -> Collections.unmodifiableList(
                        all.subList(i, Math.min(i + n, all.size()))));
    }

    // -----------------------------------------------------------------------
    // interleave
    // -----------------------------------------------------------------------

    /**
     * Interleave elements from two streams alternately, stopping at the
     * shorter one.
     *
     * <pre>{@code
     * StreamUtils.interleave(Stream.of(1, 3, 5), Stream.of(2, 4, 6))
     *            .forEach(System.out::print);
     * // 1 2 3 4 5 6
     * }</pre>
     */
    public static <T> Stream<T> interleave(Stream<T> a, Stream<T> b) {
        return zip(a, b, (x, y) -> Stream.of(x, y)).flatMap(s -> s);
    }
}

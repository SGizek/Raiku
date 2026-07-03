using System;
using System.Collections.Generic;
using System.Linq;

namespace Raiku.SharpUtils;

/// <summary>
/// Extension methods for <see cref="IEnumerable{T}"/>.
/// </summary>
public static class EnumerableExtensions
{
    // -----------------------------------------------------------------------
    // Chunk
    // -----------------------------------------------------------------------

    /// <summary>
    /// Splits <paramref name="source"/> into non-overlapping chunks of at most
    /// <paramref name="size"/> elements each.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="size"/> is less than 1.
    /// </exception>
    public static IEnumerable<IReadOnlyList<T>> Chunk<T>(
        this IEnumerable<T> source, int size)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (size < 1) throw new ArgumentOutOfRangeException(nameof(size), "Chunk size must be >= 1.");

        var buffer = new List<T>(size);
        foreach (var item in source)
        {
            buffer.Add(item);
            if (buffer.Count == size)
            {
                yield return buffer.AsReadOnly();
                buffer = new List<T>(size);
            }
        }
        if (buffer.Count > 0)
            yield return buffer.AsReadOnly();
    }

    // -----------------------------------------------------------------------
    // Windowed
    // -----------------------------------------------------------------------

    /// <summary>
    /// Returns a sequence of overlapping windows of exactly <paramref name="size"/>
    /// elements slid over <paramref name="source"/> one step at a time.
    /// </summary>
    public static IEnumerable<IReadOnlyList<T>> Windowed<T>(
        this IEnumerable<T> source, int size)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (size < 1) throw new ArgumentOutOfRangeException(nameof(size), "Window size must be >= 1.");

        var buffer = new Queue<T>(size);
        foreach (var item in source)
        {
            buffer.Enqueue(item);
            if (buffer.Count == size)
            {
                yield return buffer.ToList().AsReadOnly();
                buffer.Dequeue();
            }
        }
    }

    // -----------------------------------------------------------------------
    // DistinctBy (backport / standalone for older runtimes)
    // -----------------------------------------------------------------------

    /// <summary>
    /// Returns distinct elements from <paramref name="source"/> using a key selector.
    /// First occurrence wins.
    /// </summary>
    public static IEnumerable<T> DistinctByKey<T, TKey>(
        this IEnumerable<T> source,
        Func<T, TKey> keySelector)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(keySelector);

        var seen = new HashSet<TKey>();
        foreach (var item in source)
        {
            if (seen.Add(keySelector(item)))
                yield return item;
        }
    }

    // -----------------------------------------------------------------------
    // ForEach
    // -----------------------------------------------------------------------

    /// <summary>
    /// Executes <paramref name="action"/> for each element in the sequence.
    /// </summary>
    public static void ForEach<T>(this IEnumerable<T> source, Action<T> action)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(action);
        foreach (var item in source) action(item);
    }

    // -----------------------------------------------------------------------
    // None
    // -----------------------------------------------------------------------

    /// <summary>Returns true if no element satisfies <paramref name="predicate"/>.</summary>
    public static bool None<T>(this IEnumerable<T> source, Func<T, bool> predicate)
        => !source.Any(predicate);
}

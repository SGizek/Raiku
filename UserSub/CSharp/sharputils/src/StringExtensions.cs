using System;
using System.Globalization;
using System.Text;

namespace Raiku.SharpUtils;

/// <summary>
/// Extension methods for <see cref="string"/>.
/// </summary>
public static class StringExtensions
{
    // -----------------------------------------------------------------------
    // Guard helpers
    // -----------------------------------------------------------------------

    /// <summary>
    /// Throws <see cref="ArgumentNullException"/> if the string is null, empty,
    /// or consists only of white-space characters.
    /// </summary>
    public static string RequireNonWhiteSpace(this string? value, string paramName = "value")
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentNullException(paramName, "Value must not be null or white-space.");
        return value;
    }

    // -----------------------------------------------------------------------
    // Truncate
    // -----------------------------------------------------------------------

    /// <summary>
    /// Returns the first <paramref name="maxLength"/> characters of
    /// <paramref name="source"/>, appending <paramref name="suffix"/> when
    /// truncation occurs.
    /// </summary>
    public static string Truncate(this string source, int maxLength, string suffix = "...")
    {
        ArgumentNullException.ThrowIfNull(source);
        if (maxLength < 0) throw new ArgumentOutOfRangeException(nameof(maxLength));
        if (source.Length <= maxLength) return source;
        int cut = Math.Max(0, maxLength - suffix.Length);
        return source[..cut] + suffix;
    }

    // -----------------------------------------------------------------------
    // ToTitleCase
    // -----------------------------------------------------------------------

    /// <summary>
    /// Converts a string to Title Case using the invariant culture.
    /// "hello world" → "Hello World"
    /// </summary>
    public static string ToTitleCase(this string source)
    {
        ArgumentNullException.ThrowIfNull(source);
        return CultureInfo.InvariantCulture.TextInfo.ToTitleCase(source.ToLowerInvariant());
    }

    // -----------------------------------------------------------------------
    // Repeat
    // -----------------------------------------------------------------------

    /// <summary>
    /// Returns <paramref name="source"/> repeated <paramref name="count"/> times.
    /// </summary>
    public static string Repeat(this string source, int count)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (count < 0) throw new ArgumentOutOfRangeException(nameof(count));
        if (count == 0 || source.Length == 0) return string.Empty;
        var sb = new StringBuilder(source.Length * count);
        for (int i = 0; i < count; i++) sb.Append(source);
        return sb.ToString();
    }

    // -----------------------------------------------------------------------
    // CountOccurrences
    // -----------------------------------------------------------------------

    /// <summary>
    /// Counts the number of non-overlapping occurrences of
    /// <paramref name="substring"/> in <paramref name="source"/>.
    /// </summary>
    public static int CountOccurrences(this string source, string substring,
        StringComparison comparison = StringComparison.Ordinal)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (string.IsNullOrEmpty(substring)) return 0;

        int count = 0, index = 0;
        while ((index = source.IndexOf(substring, index, comparison)) >= 0)
        {
            count++;
            index += substring.Length;
        }
        return count;
    }

    // -----------------------------------------------------------------------
    // IsNullOrEmpty / IsNullOrWhiteSpace as instance methods
    // -----------------------------------------------------------------------

    /// <summary>Returns true if the string is null or empty.</summary>
    public static bool IsNullOrEmpty(this string? source) =>
        string.IsNullOrEmpty(source);

    /// <summary>Returns true if the string is null, empty, or white-space only.</summary>
    public static bool IsNullOrWhiteSpace(this string? source) =>
        string.IsNullOrWhiteSpace(source);
}

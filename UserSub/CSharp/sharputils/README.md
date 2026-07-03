# sharputils

Utility extension methods for .NET 8+ collections and strings.

## Installation

```bash
raiku install sharputils
```

## Usage

```csharp
using Raiku.SharpUtils;

// Collection extensions
var chunks = new[] {1,2,3,4,5}.Chunk(2).ToList();
// [[1,2], [3,4], [5]]

var windows = new[] {1,2,3,4,5}.Windowed(3).ToList();
// [[1,2,3], [2,3,4], [3,4,5]]

var distinct = new[] {"a","b","a","c"}.DistinctByKey(x => x).ToList();
// ["a","b","c"]

// String extensions
"hello world".ToTitleCase();          // "Hello World"
"long text here".Truncate(8);         // "long ..."
"ab".Repeat(3);                       // "ababab"
"abcabc".CountOccurrences("abc");     // 2
```

## License

MIT

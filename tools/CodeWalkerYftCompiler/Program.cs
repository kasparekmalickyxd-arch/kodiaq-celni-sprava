using CodeWalker.GameFiles;
using System.Text;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: CodeWalkerYftCompiler <input.yft.xml> <output.yft> [roundtrip.xml]");
    return 2;
}

var input = Path.GetFullPath(args[0]);
var output = Path.GetFullPath(args[1]);
var roundtrip = args.Length >= 3 ? Path.GetFullPath(args[2]) : null;

if (!File.Exists(input))
{
    Console.Error.WriteLine($"Input XML not found: {input}");
    return 3;
}

Directory.CreateDirectory(Path.GetDirectoryName(output)!);
RpfManager.IsGen9 = false;

var xml = File.ReadAllText(input, Encoding.UTF8);
var yft = XmlYft.GetYft(xml, Path.GetDirectoryName(input)!);
if (yft?.Fragment == null)
{
    Console.Error.WriteLine("CodeWalker failed to create a fragment from XML.");
    return 4;
}

var bytes = yft.Save();
if (bytes == null || bytes.Length < 10000)
{
    Console.Error.WriteLine($"Compiled YFT is unexpectedly small: {bytes?.Length ?? 0} bytes");
    return 5;
}
File.WriteAllBytes(output, bytes);
Console.WriteLine($"Compiled {Path.GetFileName(output)}: {bytes.Length} bytes");

// Parse the freshly compiled binary again with CodeWalker itself. This catches
// malformed resource pointers/blocks before the file is handed to FiveM.
var verify = new YftFile();
verify.Load(bytes);
if (!verify.Loaded || verify.Fragment == null || verify.Fragment.Drawable == null)
{
    Console.Error.WriteLine("Roundtrip binary parse failed.");
    return 6;
}

var rtXml = YftXml.GetXml(verify, Path.GetDirectoryName(output)!);
if (string.IsNullOrWhiteSpace(rtXml) || !rtXml.Contains("<Fragment>"))
{
    Console.Error.WriteLine("Roundtrip XML export failed.");
    return 7;
}

if (roundtrip != null)
{
    Directory.CreateDirectory(Path.GetDirectoryName(roundtrip)!);
    File.WriteAllText(roundtrip, rtXml, Encoding.UTF8);
    Console.WriteLine($"Roundtrip XML: {roundtrip}");
}

return 0;

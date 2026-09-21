// Read-only Word opening and PDF export check.
// Compile with .NET Framework csc, references System.Core.dll and Microsoft.CSharp.dll.
// Usage: check_feedback_word.exe INPUT.docx TEMP_OUTPUT.pdf
using System;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
class WordCheck {
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
 static int Main(string[] args) {
  Console.OutputEncoding=new System.Text.UTF8Encoding(false);
  dynamic app=null; dynamic doc=null; bool own=false;
  try {
   var before=Process.GetProcessesByName("WINWORD").Select(p=>p.Id).ToArray();
   app=Activator.CreateInstance(Type.GetTypeFromProgID("Word.Application"));
   string version=app.Version;
   var created=Process.GetProcessesByName("WINWORD").Where(p=>!before.Contains(p.Id)).ToArray();
   int pid=created.Length==1?created[0].Id:0;
   own=pid!=0;
   Console.WriteLine("WORD_PID="+pid+" NEW_INSTANCE="+own);
   if(!own || app.Documents.Count!=0) throw new Exception("Word did not provide an isolated empty instance; stopping without modifying it.");
   app.Visible=false;app.DisplayAlerts=0;
   doc=app.Documents.Open(FileName:args[0],ConfirmConversions:false,ReadOnly:true,AddToRecentFiles:false,Visible:false,OpenAndRepair:false,NoEncodingDialog:true);
   Console.WriteLine("OPEN_OK="+doc.Name);
   doc.Repaginate();
   doc.ExportAsFixedFormat(OutputFileName:args[1],ExportFormat:17,OpenAfterExport:false);
   Console.WriteLine("PDF_OK="+args[1]);
   doc.Close(SaveChanges:0);doc=null;
   return 0;
  } catch(Exception e) {Console.WriteLine("ERROR="+e.Message);return 1;}
  finally {if(doc!=null)try{doc.Close(SaveChanges:0);}catch{} if(own&&app!=null)try{app.Quit(SaveChanges:0);}catch{} if(app!=null)try{Marshal.FinalReleaseComObject(app);}catch{} }
 }
}

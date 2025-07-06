import { useEffect, useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
//import { oneDark } from '@uiw/codemirror-theme-one-dark';

export default function CodeEditor({ code, setCode }: { code: string, setCode: (value: string) => void }) {
  return (
    <CodeMirror
      value={code}
      //height="300px"
      style={{ height: '100%' }}
      //theme={oneDark}
      extensions={[python()]}
      onChange={(value) => setCode(value)}
      basicSetup={{
        lineNumbers: true,
        highlightActiveLine: true,
        bracketMatching: true,
        tabSize: 2,
      }}
    />
  );
}
<script lang="ts">
	import { Marked } from 'marked';
	import hljs from 'highlight.js/lib/core';
	import typescript from 'highlight.js/lib/languages/typescript';
	import python from 'highlight.js/lib/languages/python';
	import bash from 'highlight.js/lib/languages/bash';
	import json from 'highlight.js/lib/languages/json';
	import xml from 'highlight.js/lib/languages/xml';
	import css from 'highlight.js/lib/languages/css';

	hljs.registerLanguage('typescript', typescript);
	hljs.registerLanguage('javascript', typescript);
	hljs.registerLanguage('ts', typescript);
	hljs.registerLanguage('js', typescript);
	hljs.registerLanguage('python', python);
	hljs.registerLanguage('py', python);
	hljs.registerLanguage('bash', bash);
	hljs.registerLanguage('shell', bash);
	hljs.registerLanguage('sh', bash);
	hljs.registerLanguage('zsh', bash);
	hljs.registerLanguage('json', json);
	hljs.registerLanguage('html', xml);
	hljs.registerLanguage('xml', xml);
	hljs.registerLanguage('svelte', xml);
	hljs.registerLanguage('css', css);

	let { content, streaming = false }: { content: string; streaming?: boolean } = $props();

	const marked = new Marked({
		gfm: true,
		breaks: true
	});

	marked.use({
		renderer: {
			code({ text, lang }: { text: string; lang?: string }) {
				const language = lang && hljs.getLanguage(lang) ? lang : undefined;
				const highlighted = language
					? hljs.highlight(text, { language }).value
					: escapeHtml(text);
				const langLabel = lang ? `<span class="code-lang">${lang}</span>` : '';
				return `<pre class="hljs-pre">${langLabel}<code class="hljs${language ? ` language-${language}` : ''}">${highlighted}</code></pre>`;
			}
		}
	});

	function escapeHtml(str: string): string {
		return str
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;');
	}

	const html = $derived(marked.parse(content) as string);
</script>

<div class="markdown-body">
	{@html html}
	{#if streaming}
		<span class="streaming-cursor"></span>
	{/if}
</div>

# Privacy

The Coze IDE adapter renders Markdown inside the Coze execution environment and
uploads the generated image to the official Coze file API. It then calls the
user-configured file-resolution workflow in the same Coze account.

The renderer does not send Markdown to an LLM, an external image-generation
service or an external image host. Cold starts download a public runtime bundle
containing only code and open-source fonts. Fonts are bundled and require no
runtime font-service request.

Temporary request files are removed when the invocation finishes. Runtime code
and fonts may remain cached under `/tmp`. The adapter's own logs contain stages,
file sizes, timing and bounded error messages, not the API token or Markdown.
The platform may retain workflow inputs and uploaded files under its own policies;
input credentials can therefore be visible in platform execution records.

No analytics, advertising, payments or subscriptions are included. Do not publish
private workflow configuration or real credentials with this installation kit.

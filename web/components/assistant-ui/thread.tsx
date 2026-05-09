import {
  ComposerAddAttachment,
  ComposerAttachments,
  UserMessageAttachments,
} from "@/components/assistant-ui/attachment";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { Reasoning } from "@/components/assistant-ui/reasoning";
import { ToolFallback } from "@/components/assistant-ui/tool-fallback";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  ActionBarMorePrimitive,
  ActionBarPrimitive,
  AuiIf,
  BranchPickerPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAuiState,
  useThreadRuntime,
} from "@assistant-ui/react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  DownloadIcon,
  FileSearchIcon,
  FilePenIcon,
  FileX2Icon,
  GitPullRequestIcon,
  HistoryIcon,
  MoreHorizontalIcon,
  PencilIcon,
  RefreshCwIcon,
  SquareIcon,
  WrenchIcon,
} from "lucide-react";
import { type FC, type FormEvent, useEffect, useState } from "react";

export const Thread: FC = () => {
  return (
    <ThreadPrimitive.Root
      className="aui-root aui-thread-root @container flex h-full flex-col bg-background"
      style={{
        ["--thread-max-width" as string]: "44rem",
        ["--composer-radius" as string]: "24px",
        ["--composer-padding" as string]: "10px",
      }}
    >
      <ThreadPrimitive.Viewport
        turnAnchor="top"
        data-slot="aui_thread-viewport"
        className="relative flex flex-1 flex-col overflow-x-auto overflow-y-scroll scroll-smooth"
      >
        <div className="mx-auto flex w-full max-w-(--thread-max-width) flex-1 flex-col px-4 pt-4">
          <AuiIf condition={(s) => s.thread.isEmpty}>
            <ThreadWelcome />
          </AuiIf>

          <div
            data-slot="aui_message-group"
            className="mb-10 flex flex-col gap-y-8 empty:hidden"
          >
            <ThreadPrimitive.Messages>
              {() => <ThreadMessage />}
            </ThreadPrimitive.Messages>
          </div>

          <ThreadPrimitive.ViewportFooter className="aui-thread-viewport-footer sticky bottom-0 mt-auto flex flex-col gap-4 overflow-visible rounded-t-(--composer-radius) bg-background pb-4 md:pb-6">
            <ThreadScrollToBottom />
            <Composer />
          </ThreadPrimitive.ViewportFooter>
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const ThreadMessage: FC = () => {
  const role = useAuiState((s) => s.message.role);
  const isEditing = useAuiState((s) => s.message.composer.isEditing);

  if (isEditing) return <EditComposer />;
  if (role === "user") return <UserMessage />;
  return <AssistantMessage />;
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="aui-thread-scroll-to-bottom absolute -top-12 z-10 self-center rounded-full p-4 disabled:invisible dark:border-border dark:bg-background dark:hover:bg-accent"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ThreadWelcome: FC = () => {
  return (
    <div className="aui-thread-welcome-root my-auto flex grow flex-col">
      <div className="flex w-full grow flex-col items-center justify-center px-4">
        <div className="flex size-full flex-col justify-center">
          <h1 className="fade-in slide-in-from-bottom-1 animate-in fill-mode-both font-semibold text-2xl duration-200">
            Portfolio MCP
          </h1>
          <p className="fade-in slide-in-from-bottom-1 animate-in fill-mode-both text-muted-foreground text-xl delay-75 duration-200">
            Interact with your GitHub repository
          </p>
        </div>
      </div>
      <MCPQuickActions />
    </div>
  );
};

/** Quick action cards shown on the welcome screen. */
const MCPQuickActions: FC = () => {
  return (
    <div className="grid w-full gap-3 pb-4 @md:grid-cols-2">
      <ListToolsAction />
      <ReadFileAction />
      <GetFileHistoryAction />
      <DeleteFileAction />
      <UpdateFileAction />
      <CreatePRAction />
    </div>
  );
};

const ListToolsAction: FC = () => {
  const thread = useThreadRuntime();
  const send = () =>
    thread.append({
      role: "user",
      content: [{ type: "text", text: "list tools" }],
    });

  return (
    <button
      type="button"
      onClick={send}
      className="cursor-pointer fade-in slide-in-from-bottom-2 animate-in fill-mode-both flex flex-col items-start gap-1 rounded-3xl border bg-background px-4 py-3 text-left text-sm transition-colors hover:bg-muted duration-200"
    >
      <span className="flex items-center gap-2 font-medium">
        <WrenchIcon className="size-4 shrink-0 text-muted-foreground" />
        List available tools
      </span>
      <span className="text-muted-foreground">
        Show all MCP server capabilities
      </span>
    </button>
  );
};

const ReadFileAction: FC = () => {
  const thread = useThreadRuntime();
  const [path, setPath] = useState("");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = path.trim();
    if (!trimmed) return;
    thread.append({
      role: "user",
      content: [{ type: "text", text: `read ${trimmed}` }],
    });
    setPath("");
  };

  return (
    <form
      onSubmit={submit}
      className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both flex flex-col gap-2 rounded-3xl border bg-background px-4 py-3 text-sm duration-200 delay-75"
    >
      <span className="flex items-center gap-2 font-medium">
        <FileSearchIcon className="size-4 shrink-0 text-muted-foreground" />
        Read a file
      </span>
      <div className="flex gap-2">
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="e.g. README.md or src/index.ts"
          className="min-w-0 flex-1 rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
        />
        <Button
          type="submit"
          size="sm"
          variant="default"
          disabled={!path.trim()}
          className="cursor-pointer rounded-xl"
        >
          Read
        </Button>
      </div>
    </form>
  );
};

const UpdateFileAction: FC = () => {
  const thread = useThreadRuntime();
  const [path, setPath] = useState("");
  const [commitMsg, setCommitMsg] = useState("");
  const [content, setContent] = useState("");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmedPath = path.trim();
    const trimmedCommit = commitMsg.trim();
    const trimmedContent = content.trim();
    if (!trimmedPath || !trimmedCommit || !trimmedContent) return;
    thread.append({
      role: "user",
      content: [
        {
          type: "text",
          text: `update ${trimmedPath} commit: ${trimmedCommit} content: ${trimmedContent}`,
        },
      ],
    });
    setPath("");
    setCommitMsg("");
    setContent("");
  };

  const isValid = path.trim() && commitMsg.trim() && content.trim();

  return (
    <form
      onSubmit={submit}
      className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both col-span-full flex flex-col gap-2 rounded-3xl border bg-background px-4 py-3 text-sm duration-200 delay-100"
    >
      <span className="flex items-center gap-2 font-medium">
        <FilePenIcon className="size-4 shrink-0 text-muted-foreground" />
        Update a file
      </span>
      <div className="grid gap-2 @md:grid-cols-2">
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="File path (e.g. README.md)"
          className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
        />
        <input
          type="text"
          value={commitMsg}
          onChange={(e) => setCommitMsg(e.target.value)}
          placeholder="Commit message"
          className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
        />
      </div>
      <div className="flex gap-2">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="New file content..."
          rows={4}
          className="min-w-0 flex-1 resize-y rounded-xl border bg-muted/50 px-3 py-1.5 font-mono text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
        />
      </div>
      <div className="flex justify-end">
        <Button
          type="submit"
          size="sm"
          variant="default"
          disabled={!isValid}
          className="rounded-xl"
        >
          Update
        </Button>
      </div>
    </form>
  );
};


const GetFileHistoryAction: FC = () => {
  const thread = useThreadRuntime();
  const [path, setPath] = useState("");
  const [limit, setLimit] = useState("10");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = path.trim();
    if (!trimmed) return;
    const n = parseInt(limit, 10);
    const limitPart = n && n !== 10 ? ` limit: ${n}` : "";
    thread.append({
      role: "user",
      content: [{ type: "text", text: `history ${trimmed}${limitPart}` }],
    });
    setPath("");
    setLimit("10");
  };

  return (
    <form
      onSubmit={submit}
      className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both flex flex-col gap-2 rounded-3xl border bg-background px-4 py-3 text-sm duration-200 delay-125"
    >
      <span className="flex items-center gap-2 font-medium">
        <HistoryIcon className="size-4 shrink-0 text-muted-foreground" />
        File history
      </span>
      <div className="flex gap-2">
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="e.g. README.md or src/index.ts"
          className="min-w-0 flex-1 rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
        />
        <input
          type="number"
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
          min={1}
          max={100}
          className="w-16 rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/20"
          title="Max commits"
        />
        <Button
          type="submit"
          size="sm"
          variant="default"
          disabled={!path.trim()}
          className="cursor-pointer rounded-xl"
        >
          History
        </Button>
      </div>
    </form>
  );
};


const DeleteFileAction: FC = () => {
  const thread = useThreadRuntime();
  const [path, setPath] = useState("");
  const [commitMsg, setCommitMsg] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmedPath = path.trim();
    const trimmedCommit = commitMsg.trim();
    if (!trimmedPath || !trimmedCommit || !confirmed) return;
    thread.append({
      role: "user",
      content: [
        {
          type: "text",
          text: `delete ${trimmedPath} commit: ${trimmedCommit}`,
        },
      ],
    });
    setPath("");
    setCommitMsg("");
    setConfirmed(false);
  };

  const isValid = path.trim() && commitMsg.trim() && confirmed;

  return (
    <form
      onSubmit={submit}
      className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both flex flex-col gap-2 rounded-3xl border border-destructive/30 bg-background px-4 py-3 text-sm duration-200 delay-150"
    >
      <span className="flex items-center gap-2 font-medium text-destructive">
        <FileX2Icon className="size-4 shrink-0" />
        Delete a file
      </span>
      <div className="grid gap-2 @md:grid-cols-2">
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="File path (e.g. old/file.md)"
          className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-destructive focus:ring-2 focus:ring-destructive/20"
        />
        <input
          type="text"
          value={commitMsg}
          onChange={(e) => setCommitMsg(e.target.value)}
          placeholder="Commit message"
          className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-destructive focus:ring-2 focus:ring-destructive/20"
        />
      </div>
      <label className="flex cursor-pointer items-center gap-2 text-muted-foreground text-xs select-none">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
          className="accent-destructive"
        />
        I understand this will permanently delete the file
      </label>
      <div className="flex justify-end">
        <Button
          type="submit"
          size="sm"
          variant="destructive"
          disabled={!isValid}
          className="rounded-xl"
        >
          Delete
        </Button>
      </div>
    </form>
  );
};


const CreatePRAction: FC = () => {
  const thread = useThreadRuntime();
  const [title, setTitle] = useState("");
  const [head, setHead] = useState("");
  const [base, setBase] = useState("main");
  const [body, setBody] = useState("");
  const [branches, setBranches] = useState<string[]>([]);

  // Fetch available branches once on mount
  useEffect(() => {
    fetch("/api/branches")
      .then((r) => r.json())
      .then((d) => {
        if (Array.isArray(d.branches)) setBranches(d.branches);
      })
      .catch(() => {});
  }, []);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const t = title.trim();
    const h = head.trim();
    const b = base.trim();
    if (!t || !h || !b) return;
    const bodyPart = body.trim() ? ` body: ${body.trim()}` : "";
    thread.append({
      role: "user",
      content: [
        {
          type: "text",
          text: `create pr title: ${t} from: ${h} into: ${b}${bodyPart}`,
        },
      ],
    });
    setTitle("");
    setHead("");
    setBase("main");
    setBody("");
  };

  const isValid = title.trim() && head.trim() && base.trim();

  const selectClass =
    "rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/20 cursor-pointer";

  return (
    <form
      onSubmit={submit}
      className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both col-span-full flex flex-col gap-2 rounded-3xl border bg-background px-4 py-3 text-sm duration-200 delay-200"
    >
      <span className="flex items-center gap-2 font-medium">
        <GitPullRequestIcon className="size-4 shrink-0 text-muted-foreground" />
        Create a pull request
      </span>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="PR title"
        className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
      />
      <div className="grid gap-2 @md:grid-cols-2">
        {branches.length > 0 ? (
          <>
            <select value={head} onChange={(e) => setHead(e.target.value)} className={selectClass}>
              <option value="">Head branch (from)…</option>
              {branches.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
            <select value={base} onChange={(e) => setBase(e.target.value)} className={selectClass}>
              <option value="">Base branch (into)…</option>
              {branches.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </>
        ) : (
          <>
            <input
              type="text"
              value={head}
              onChange={(e) => setHead(e.target.value)}
              placeholder="Head branch (from)"
              className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
            />
            <input
              type="text"
              value={base}
              onChange={(e) => setBase(e.target.value)}
              placeholder="Base branch (into)"
              className="rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
            />
          </>
        )}
      </div>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="PR description (optional)"
        rows={2}
        className="resize-y rounded-xl border bg-muted/50 px-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/20"
      />
      <div className="flex justify-end">
        <Button
          type="submit"
          size="sm"
          variant="default"
          disabled={!isValid}
          className="rounded-xl"
        >
          Open PR
        </Button>
      </div>
    </form>
  );
};


const Composer: FC = () => {
  return (
    <ComposerPrimitive.Root className="aui-composer-root relative flex w-full flex-col">
      <ComposerPrimitive.AttachmentDropzone asChild>
        <div
          data-slot="aui_composer-shell"
          className="flex w-full flex-col gap-2 rounded-(--composer-radius) border bg-background p-(--composer-padding) transition-shadow focus-within:border-ring/75 focus-within:ring-2 focus-within:ring-ring/20 data-[dragging=true]:border-ring data-[dragging=true]:border-dashed data-[dragging=true]:bg-accent/50"
        >
          <ComposerAttachments />
          <ComposerPrimitive.Input
            placeholder="Send a message... (e.g. read README.md)"
            className="aui-composer-input max-h-32 min-h-10 w-full resize-none bg-transparent px-1.75 py-1 text-sm outline-none placeholder:text-muted-foreground/80"
            rows={1}
            autoFocus
            aria-label="Message input"
          />
          <ComposerAction />
        </div>
      </ComposerPrimitive.AttachmentDropzone>
    </ComposerPrimitive.Root>
  );
};

const ComposerAction: FC = () => {
  return (
    <div className="aui-composer-action-wrapper relative flex items-center justify-between">
      <ComposerAddAttachment />
      <AuiIf condition={(s) => !s.thread.isRunning}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip="Send message"
            side="bottom"
            type="button"
            variant="default"
            size="icon"
            className="aui-composer-send size-8 rounded-full"
            aria-label="Send message"
          >
            <ArrowUpIcon className="aui-composer-send-icon size-4" />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </AuiIf>
      <AuiIf condition={(s) => s.thread.isRunning}>
        <ComposerPrimitive.Cancel asChild>
          <Button
            type="button"
            variant="default"
            size="icon"
            className="aui-composer-cancel size-8 rounded-full"
            aria-label="Stop generating"
          >
            <SquareIcon className="aui-composer-cancel-icon size-3 fill-current" />
          </Button>
        </ComposerPrimitive.Cancel>
      </AuiIf>
    </div>
  );
};

const MessageError: FC = () => {
  return (
    <MessagePrimitive.Error>
      <ErrorPrimitive.Root className="aui-message-error-root mt-2 rounded-md border border-destructive bg-destructive/10 p-3 text-destructive text-sm dark:bg-destructive/5 dark:text-red-200">
        <ErrorPrimitive.Message className="aui-message-error-message line-clamp-2" />
      </ErrorPrimitive.Root>
    </MessagePrimitive.Error>
  );
};

const AssistantMessage: FC = () => {
  const ACTION_BAR_PT = "pt-1.5";
  const ACTION_BAR_HEIGHT = `-mb-7.5 min-h-7.5 ${ACTION_BAR_PT}`;

  return (
    <MessagePrimitive.Root
      data-slot="aui_assistant-message-root"
      data-role="assistant"
      className="fade-in slide-in-from-bottom-1 relative animate-in duration-150"
    >
      <div
        data-slot="aui_assistant-message-content"
        className="wrap-break-word px-2 text-foreground leading-relaxed"
      >
        <MessagePrimitive.Parts>
          {({ part }) => {
            if (part.type === "text") return <MarkdownText />;
            if (part.type === "reasoning") return <Reasoning {...part} />;
            if (part.type === "tool-call")
              return part.toolUI ?? <ToolFallback {...part} />;
            return null;
          }}
        </MessagePrimitive.Parts>
        <MessageError />
      </div>

      <div
        data-slot="aui_assistant-message-footer"
        className={cn("ml-2 flex items-center", ACTION_BAR_HEIGHT)}
      >
        <BranchPicker />
        <AssistantActionBar />
      </div>
    </MessagePrimitive.Root>
  );
};

const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="aui-assistant-action-bar-root col-start-3 row-start-2 -ml-1 flex gap-1 text-muted-foreground"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <AuiIf condition={(s) => s.message.isCopied}>
            <CheckIcon />
          </AuiIf>
          <AuiIf condition={(s) => !s.message.isCopied}>
            <CopyIcon />
          </AuiIf>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
      <ActionBarMorePrimitive.Root>
        <ActionBarMorePrimitive.Trigger asChild>
          <TooltipIconButton
            tooltip="More"
            className="data-[state=open]:bg-accent"
          >
            <MoreHorizontalIcon />
          </TooltipIconButton>
        </ActionBarMorePrimitive.Trigger>
        <ActionBarMorePrimitive.Content
          side="bottom"
          align="start"
          className="aui-action-bar-more-content z-50 min-w-32 overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
        >
          <ActionBarPrimitive.ExportMarkdown asChild>
            <ActionBarMorePrimitive.Item className="aui-action-bar-more-item flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground">
              <DownloadIcon className="size-4" />
              Export as Markdown
            </ActionBarMorePrimitive.Item>
          </ActionBarPrimitive.ExportMarkdown>
        </ActionBarMorePrimitive.Content>
      </ActionBarMorePrimitive.Root>
    </ActionBarPrimitive.Root>
  );
};

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      data-slot="aui_user-message-root"
      className="fade-in slide-in-from-bottom-1 grid animate-in auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] content-start gap-y-2 px-2 duration-150 [&:where(>*)]:col-start-2"
      data-role="user"
    >
      <UserMessageAttachments />

      <div className="aui-user-message-content-wrapper relative col-start-2 min-w-0">
        <div className="aui-user-message-content wrap-break-word peer rounded-2xl bg-muted px-4 py-2.5 text-foreground empty:hidden">
          <MessagePrimitive.Parts />
        </div>
        <div className="aui-user-action-bar-wrapper absolute top-1/2 left-0 -translate-x-full -translate-y-1/2 pr-2 peer-empty:hidden">
          <UserActionBar />
        </div>
      </div>

      <BranchPicker
        data-slot="aui_user-branch-picker"
        className="col-span-full col-start-1 row-start-3 -mr-1 justify-end"
      />
    </MessagePrimitive.Root>
  );
};

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="aui-user-action-bar-root flex flex-col items-end"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit" className="aui-user-action-edit p-4">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
};

const EditComposer: FC = () => {
  return (
    <MessagePrimitive.Root
      data-slot="aui_edit-composer-wrapper"
      className="flex flex-col px-2"
    >
      <ComposerPrimitive.Root className="aui-edit-composer-root ml-auto flex w-full max-w-[85%] flex-col rounded-2xl bg-muted">
        <ComposerPrimitive.Input
          className="aui-edit-composer-input min-h-14 w-full resize-none bg-transparent p-4 text-foreground text-sm outline-none"
          autoFocus
        />
        <div className="aui-edit-composer-footer mx-3 mb-3 flex items-center gap-2 self-end">
          <ComposerPrimitive.Cancel asChild>
            <Button variant="ghost" size="sm">
              Cancel
            </Button>
          </ComposerPrimitive.Cancel>
          <ComposerPrimitive.Send asChild>
            <Button size="sm">Update</Button>
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
    </MessagePrimitive.Root>
  );
};

const BranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn(
        "aui-branch-picker-root mr-2 -ml-2 inline-flex items-center text-muted-foreground text-xs",
        className,
      )}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="aui-branch-picker-state font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};

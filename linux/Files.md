# File Manipulation

> **Previous:** [The Filesystem](Filesystem.md)

Practical file operations: understanding timestamps, identifying file types, viewing content, and creating, copying, moving, and deleting files.

---

## Timestamps

Every file tracks three timestamps:

| Timestamp     | Abbrev  | Updated when...                                       |
| ------------- | ------- | ----------------------------------------------------- |
| Access time   | `atime` | The file is read                                      |
| Modified time | `mtime` | The file's content changes                            |
| Changed time  | `ctime` | File metadata changes (permissions, ownership, links) |

### Viewing Timestamps

```bash
stat file          # full timestamp details
ls -l              # standard listing (mtime)
ls -lt             # sort by mtime
ls -lu             # show atime
ls -ltu            # sort by atime
ls -lc             # show and sort by ctime
ls --full-time     # full timestamp format (ls may abbreviate)
```

### Changing Timestamps with `touch`

`touch` updates timestamps. If the file doesn't exist, it creates it.

```bash
touch file                        # update atime and mtime to now
touch -a file                     # update atime only
touch -m file                     # update mtime only
touch -m -t 20251022110000 file   # set mtime to a specific time
touch -d "2025-10-22 11:00:00" file
touch target -r reference         # copy timestamps from another file
```

> `ctime` cannot be set directly — it updates automatically whenever metadata changes.

---

## File Types

Linux identifies files by their **content headers**, not their extension. Renaming `video.mp4` to `video.txt` doesn't change what the file actually is.

```bash
file photo.jpg        # identify a single file
file /etc/*           # identify every file in a directory
```

### Type Indicators in `ls -l`

The first character of each line shows the file type:

| Character | Type              |
| --------- | ----------------- |
| `-`       | Regular file      |
| `d`       | Directory         |
| `l`       | Symbolic link     |
| `b`       | Block device      |
| `c`       | Character device  |
| `s`       | Socket            |
| `p`       | Named pipe (FIFO) |

### `ls -F` Symbols

| Symbol | Type          |
| ------ | ------------- |
| `/`    | Directory     |
| `@`    | Symbolic link |
| `*`    | Executable    |
| `=`    | Socket        |
| `\|`   | Named pipe    |

---

## Viewing Files

Most Linux configuration lives in plain text files under `/etc`, `/var`, and home directories. Knowing how to read them is essential.

| Command                      | Use it for                                |
| ---------------------------- | ----------------------------------------- |
| `cat file`                   | Print a short file to the terminal        |
| `cat -n file`                | Print with line numbers                   |
| `cat file1 file2 > combined` | Merge files                               |
| `less file`                  | Scroll up/down through a long file        |
| `more file`                  | Scroll forward only (older)               |
| `head file`                  | Show first 10 lines                       |
| `head -n 20 file`            | Show first 20 lines                       |
| `tail file`                  | Show last 10 lines                        |
| `tail -n 20 file`            | Show last 20 lines                        |
| `tail -n +20 file`           | Show from line 20 onward                  |
| `tail -f file`               | Follow file in real time (great for logs) |
| `watch command`              | Re-run a command every 2 seconds          |
| `watch -n 5 command`         | Re-run every 5 seconds                    |
| `watch -d command`           | Highlight changing output                 |

---

## Creating, Copying, Moving, Removing

### Create

```bash
touch file.txt          # create empty file (or update timestamps)
mkdir dir               # create directory
mkdir -v dir            # verbose
mkdir -p parent/child   # create parent directories as needed
mkdir dir1 dir2 dir3    # create multiple at once
```

### Copy

```bash
cp file1 file2          # copy file1 to file2 (overwrites if file2 exists)
cp -v file1 file2       # verbose
cp -i file1 file2       # prompt before overwrite
cp -r dir1 dir2         # recursive (copy directory)
cp -p file1 file2       # preserve ownership and timestamps
cp file1 file2 dest/    # copy multiple files to a destination
```

### Move & Rename

```bash
mv file1 file2          # rename file1 to file2
mv file dir/            # move file into directory
mv -i file1 file2       # prompt before overwrite
mv -n file1 file2       # never overwrite (abort silently)
```

### Remove

```bash
rm file                 # delete file
rm -i file              # prompt before deleting
rm -v file              # verbose
rm -r dir               # recursive (delete directory and contents)
rm -f file              # force (no prompt, no error if missing)
```

> There is no trash bin in Linux. Files removed from the terminal are gone.

### Secure Delete

`rm` only unlinks a file — the data remains on disk until overwritten. Use `shred` for sensitive files:

```bash
shred -vu -n 100 file
```

| Flag     | Meaning                           |
| -------- | --------------------------------- |
| `-v`     | Verbose                           |
| `-u`     | Remove the file after overwriting |
| `-n 100` | Overwrite 100 times               |

> Even `shred` may not fully protect secrets on SSDs or copy-on-write filesystems. Keep truly sensitive files encrypted. See [GPG](../tools/GPG.md).

---

## What to Read Next

| You want to...           | Go here                             |
| ------------------------ | ----------------------------------- |
| Review filesystem layout | [The Filesystem](Filesystem.md)     |
| Build your security lab  | [Tools & Setup](../tools/README.md) |
| Encrypt sensitive files  | [GPG](../tools/GPG.md)              |

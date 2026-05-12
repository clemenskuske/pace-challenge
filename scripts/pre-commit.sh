#!/usr/bin/env sh
set -u

cd "$(git rev-parse --show-toplevel)"

if scripts/check-short.sh
then
  exit 0
fi

cat >&2 <<'EOF'

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
KNOWN INSTANCE CHECK FAILED.

At least one guarded instance is now computed incorrectly, or the checked solver
state is otherwise unusable. Per repository policy, this hook is reverting all
staged and unstaged changes back to HEAD before aborting the commit.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

EOF

git reset --hard HEAD
git clean -fd

exit 1

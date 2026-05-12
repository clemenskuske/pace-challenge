#!/usr/bin/env sh
set -u

cd "$(git rev-parse --show-toplevel)"

if scripts/check-big.sh
then
  exit 0
fi

cat >&2 <<'EOF'

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
KNOWN OR PUBLIC INSTANCE CHECK FAILED.

At least one guarded known instance or one of the 150 public exact smoke-test
instances is now wrong, unparsable, or otherwise unusable. Per repository
policy, this hook is reverting all staged and unstaged changes back to HEAD
before aborting the commit.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

EOF

git reset --hard HEAD
git clean -fd

exit 1

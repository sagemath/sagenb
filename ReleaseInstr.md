## Steps to create a Sagenb package

Throughout the steps below, replace `<version>` with the actual version,
for example, `0.10.8.3`. Also, we will assume that
`github.org/sagemath/sagenb` is present as `upstream` remote repository
in your local `SAGENB_ROOT`.

1. Change into the sagenb git directory, and update to the latest
   `upstream/master`. We assume that all the required merges to the
   `upstream/master` have happened already and that your master is
   at a previous or current commit (same hash) of `upstream/master`;
   if not, use `git merge upstream/master` instead of `git rebase`.

    ```sh
    cd SAGENB_ROOT
    git checkout master
    git fetch upstream
    git rebase upstream/master  
    ```

1. Edit `Changes` file to highlight the main changes. Edit `setup.py` to
   update the version for Sagenb (this is *important*). Example diff:

    ```diff
    --- a/setup.py
    +++ b/setup.py
    @@ -44,7 +44,7 @@ if __name__ == '__main__':
             distutils.log.set_threshold(distutils.log.DEBUG)

         code = setup(name = 'sagenb',
    -          version     = '0.10.8.2',
    +          version     = '0.10.8.3',
               description = 'The Sage Notebook',
               license     = 'GNU General Public License (GPL) v3+',
               author      = 'William Stein et al.',                      
    ```

1. Commit the updated version change.

    ```sh
    git add Changes
    git add setup.py
    git commit -m "Update Sagenb version to <version>"
    ```

1. Create the dist directory with all the included packages.

    ```sh
    ./dist.sh
    ```

1. (Optional) If the above command was already run once, then to avoid
   downloading all the dependencies all over again, and to just repackage
   only sagenb, the following command can also be run:

    ```sh
    rm -f dist/sagenb*
    ./dist.sh -s
    ```

   Be careful to check that the ``dist`` directory still has a copy of
   each upstream package and the sagenb package; it's worth also checking
   that ``dist/sagenb-<version>.tar.gz`` only contains sagenb and not
   extra copies of the upstream files, by checking the output of

    ```sh
    tar -tzf dist/sagenb-<version>.tar.gz
    ```

1. Create the sagenb tar file for inclusion into Sage.

    ```sh
    mv dist sagenb-<version>
    tar cf sagenb-<version>.tar sagenb-<version>
    mv sagenb-<version>.tar SAGE_ROOT/upstream
    ```
    
1. Let Sage know about the new sagenb and update its checksums, and then
   try out the new sagenb and test it.  Here we are not yet committing,
   in case of any errors.

    ```sh
    cd SAGE_ROOT
    echo "<version>" > build/pkgs/sagenb/package-version.txt
    ./sage -sh -c sage-fix-pkg-checksums
    ./sage -tp --long --sagenb  # test sagenb
    make ptestlong              # test sage
    ```

1. (Optional) If you encounter errors or realize there was a mistake,
   you can try to fix them back in sagenb, after reverting the last
   change (the updated sagenb version).

    ```sh
    cd SAGENB_ROOT
    git reset --mixed  HEAD^
    <fix whatever needs fixing>
    <perhaps run tests again, from SAGE_ROOT>
    git commit -m 'Fix doctests' # or whatever is appropriate
    <edit Changes and setup.py again if necessary>
    git add Changes
    git add setup.py
    git commit
    ```

   Now return to the previous step (in `SAGE_ROOT`) as needed,
   and then proceed.

1. Now we can create a branch for the ticket `<ticket>`, commit our changes,
   and push to Trac.  Warning: do not use `git commit -a`
   unless you are sure (see `git status`) that you don't have anything else
   in your directory that shouldn't be added; otherwise do `git add` the
   correct files first.

    ```sh
    git checkout develop -b ticket/<ticket> # or "git trac create" or "git trac checkout", etc
    git commit -a -m "Upgrade sagenb to version <version>"
    ./sage -tp --long --sagenb  # test sagenb again
    make ptestlong              # test sage again if need be
    git trac push <ticket>
    ```

   You will want to upload the sagenb tar file somewhere convenient and
   put a link to it on the appropriate Trac ticket as well.

1. Now that everything is fine, update the sagenb in Github with the new
   changes.

    ```sh
    cd SAGENB_ROOT
    git tag <version>
    git push upstream master
    git checkout release
    git merge <version>
    git push upstream release
    git push upstream --tags  # This will automatically create sagenb.tar.gz in Github
    ```

1. If you encounter any difficulties, you can also look at the
   [work flow](https://gist.github.com/kini/5852091) that was shown by
   @kini long ago or see the older release instructions in README.rst

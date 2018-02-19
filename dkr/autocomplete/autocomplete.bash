if !([ -n "$(type -t _get_comp_words_by_ref)" ] && [ "$(type -t _get_comp_words_by_ref)" = function ]); then
    echo "Dkr: Please install bash autocompletions, see README" ;
fi

if [ -f $(brew --prefix)/etc/bash_completion ]; then
    . $(brew --prefix)/etc/bash_completion
fi

_dkr ()
{
    local cur opts

    _get_comp_words_by_ref -n : cur

    COMPREPLY=()
    #_get_comp_words_by_ref cur

    DOCKERS=`docker images | tail -n +2 | cut -f 1 -d' ' | paste -s -d ' ' -`
    if [ -f ~/.dkr ]; then
        ENTRYPOINTS=`egrep "^\s+-" ~/.dkr | cut -f2- -d '-' | tr -d ' ' | paste -s -d ' ' -`
        DOCKERS="$DOCKERS $ENTRYPOINTS"
    fi

    cur="${COMP_WORDS[COMP_CWORD]}"
    if [ $COMP_CWORD -eq 1 ]; then
      COMPREPLY=( $( compgen -W "$DOCKERS" -- "$cur" ) )
    else
      COMPREPLY=()
    fi
     
    __ltrim_colon_completions "$cur"

}

complete -o default -F _dkr dkr

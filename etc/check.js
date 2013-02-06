{
  "grammar": {
    "rules": [
      {
        "rhs": [
          {
            "value": {
              "repeat": "rule", 
              "plus": "+"
            }, 
            "name": "rules", 
            "force_list": null
          }, 
          "$"
        ], 
        "name": "grammar"
      }, 
      {
        "rhs": [
          {
            "value": "word", 
            "name": "ast_name", 
            "force_list": null
          }, 
          ":", 
          {
            "value": "word", 
            "name": "name", 
            "force_list": null
          }, 
          "=", 
          ">>", 
          {
            "value": "expre", 
            "name": "rhs", 
            "force_list": null
          }, 
          {
            "options": [
              ".", 
              ";"
            ]
          }, 
          ">>"
        ], 
        "name": "rule"
      }, 
      {
        "rhs": {
          "options": [
            "choice", 
            "sequence"
          ]
        }, 
        "name": "expre"
      }, 
      {
        "rhs": [
          {
            "value": "sequence", 
            "name": "options", 
            "force_list": "+"
          }, 
          {
            "repeat": [
              "|", 
              ">>", 
              {
                "value": "sequence", 
                "name": "options", 
                "force_list": null
              }
            ], 
            "plus": "+"
          }
        ], 
        "name": "choice"
      }, 
      {
        "rhs": [
          "element", 
          {
            "repeat": [
              ",", 
              "element"
            ], 
            "plus": null
          }
        ], 
        "name": "sequence"
      }, 
      {
        "rhs": {
          "options": [
            "named", 
            "override", 
            "term"
          ]
        }, 
        "name": "element"
      }, 
      {
        "rhs": [
          {
            "value": "qualified", 
            "name": "name", 
            "force_list": null
          }, 
          {
            "value": "+", 
            "name": "force_list", 
            "force_list": null
          }, 
          ":", 
          {
            "value": "element", 
            "name": "value", 
            "force_list": null
          }
        ], 
        "name": "named"
      }, 
      {
        "rhs": [
          "@", 
          "element"
        ], 
        "name": "override"
      }, 
      {
        "rhs": {
          "options": [
            "void", 
            "subexp", 
            "repeat", 
            "optional", 
            "special", 
            "kif", 
            "knot", 
            "atom"
          ]
        }, 
        "name": "term"
      }, 
      {
        "rhs": [
          "(", 
          ">>", 
          "expre", 
          ")", 
          ">>"
        ], 
        "name": "subexp"
      }, 
      {
        "rhs": [
          "{", 
          ">>", 
          {
            "value": "expre", 
            "name": "repeat", 
            "force_list": null
          }, 
          "}", 
          ">>", 
          {
            "value": {
              "options": [
                "-", 
                "+"
              ]
            }, 
            "name": "plus", 
            "force_list": null
          }, 
          ">>"
        ], 
        "name": "repeat"
      }, 
      {
        "rhs": [
          "[", 
          ">>", 
          "expre", 
          "]", 
          ">>"
        ], 
        "name": "optional"
      }, 
      {
        "rhs": [
          "?(", 
          ">>", 
          "(.*)", 
          ")?", 
          ">>"
        ], 
        "name": "special"
      }, 
      {
        "rhs": [
          "&", 
          "term"
        ], 
        "name": "kif"
      }, 
      {
        "rhs": [
          "!", 
          "term"
        ], 
        "name": "knot"
      }, 
      {
        "rhs": {
          "options": [
            "cut", 
            "token", 
            "call", 
            "pattern", 
            "eof"
          ]
        }, 
        "name": "atom"
      }, 
      {
        "rhs": "word", 
        "name": "call"
      }, 
      {
        "rhs": "()", 
        "name": "void"
      }, 
      {
        "rhs": ">>", 
        "name": "cut"
      }, 
      {
        "rhs": {
          "options": [
            [
              "\"", 
              "([^\"]|\\\\\")*", 
              "\"", 
              "|", 
              [
                "'", 
                "([^']|\\\\')*", 
                "'"
              ]
            ], 
            [
              "'", 
              "([^']|\\\\')*", 
              "'"
            ]
          ]
        }, 
        "name": "token"
      }, 
      {
        "rhs": "[-_A-Za-z0-9]+(?:\\.[-_A-Za-z0-9]+)*", 
        "name": "qualified"
      }, 
      {
        "rhs": "[-_A-Za-z0-9]+", 
        "name": "word"
      }, 
      {
        "rhs": [
          "?/", 
          ">>", 
          "(.*?)(?=/\\?)", 
          "/?"
        ], 
        "name": "pattern"
      }, 
      {
        "rhs": "$", 
        "name": "eof"
      }
    ]
  }
}
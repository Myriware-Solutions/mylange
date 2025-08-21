# Myriware Mylange

Myriware Mylange Scripting Language (MMSL) is a in-house developed
programming language which aims to teach all Myriware employees
a common scripting language that can be used on Servers, Sites, etc.

However, this is open source and anyone is allowed to use this
language. This file will cover the writing and using fo this programming language.

# Syntax

The Syntax of Mylange is easy to follow. It incorperates many different languages
and provides new syntaxes as well. First rule of thumb is that Semicolons are needed.
This is not a programming language that allows for open-ended code.
Also, brackets define code blocks which are linked to code block keywords. Also,
there are many different keywords that surround values, not just infront of.

## Variables

All variable declarations follow the same syntax:

```
{type} {varname} => {value};
```

Type are different types.

* nil : A null type value used in Myalnge.
* boolean : true OR false
* integar : a simple number : 0, 1, -2, 3, etc
* character : a single character : 'c', 'h', 'a', 'r'
* string : A group of characters : "string"
* array : A group of (one type of) values : ["Strings", "are", "fun"]
* set : Object like with key-value paires : (name=>"mylange", coolness=>10)

## Loops

Loops can contain code and loop over until a specific condition is met,
or it has completed going over an inumerable collection of values.

### For/In loops

Syntax: 

```
for <type> var in inumerable do {
    // Loop Code
};

for <type> var in inumerable do /[single line code]/;

for <type> var in inumerable do 
    /[single line code]/;
```

Takes an array, and loops the code over it.
The `var` is used for each element of the dataset.
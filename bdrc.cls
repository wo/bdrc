% !TEX program = xelatex
\ProvidesClass{bdrc}
\NeedsTeXFormat{LaTeX2e}

% parent class scrbook:
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{scrbook}}
\ProcessOptions
\LoadClass[12pt, twoside=false, a4paper, DIV=calc, headsepline, footnotes=multiple]{scrbook}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

% ============= math packages =============

% \usepackage{amsthm}
% \usepackage[fleqn, leqno]{amsmath}
% \setlength\mathindent{1.6cm}
% \everydisplay{\displayindent=1cm}
% \usepackage{amsfonts}
% \usepackage{amssymb}

% ============= additional packages =============
% 
\usepackage{enumerate} % for enumerate with roman and alphabetical labels:
\usepackage{fancyvrb,paralist}
\usepackage{multirow,rotating}
\usepackage{eqlist}
\usepackage{mdwlist}
\usepackage[english]{babel} % English language/hyphenation
\usepackage{graphicx} % for including pictures
\usepackage[table,xcdraw]{xcolor}
\usepackage{tikz}
\usepackage{scalerel} % \scaleto for tiny letters

% ============= fonts ==============
% 
\usepackage{fontspec}
\usepackage{unicode-math}
\defaultfontfeatures{Scale=MatchLowercase, Ligatures=TeX}
\setmainfont{TeX Gyre Termes}[Scale=1.0]
\setmathfont{TeX Gyre Termes Math}
\newfontfamily{\headerfont}{Utopia}
\addtokomafont{chapter}{\headerfont\bfseries}
\addtokomafont{section}{\headerfont\bfseries}

% \setkomafont{disposition}{\normalfont}

% \RedeclareSectionCommands[%
%   tocentrynumberformat=\headerfont\bfseries,
%   tocentryformat=\headerfont\bfseries,%
%   tocpagenumberformat=\headerfont\bfseries,%
% ]{chapter}

% \RedeclareSectionCommands[%
%   tocentrynumberformat=\headerfont,%
%   tocentryformat=\headerfont,%
%   tocpagenumberformat=\headerfont,%
% ]{section}

% \usepackage[osf,sc]{mathpazo} % Palatino for main text and math
%\usepackage[scaled=0.90]{helvet} % Helvetica for sans serif (scaled to match size of Palatino)
%\usepackage{newtxtext}
%\usepackage{newtxmath}
%\usepackage[scaled=0.90]{helvet} % Helvetica for sans serif (scaled to match size of Palatino)
%\usepackage{newtxmath}
%\usepackage{txfonts}
%\usepackage{fouriernc}
%\usepackage[onlytext]{MinionPro}
%\renewcommand{\sfdefault}{Myriad-LF}
%\usepackage{lmodern}
%\usepackage{libertine}
%\usepackage[libertine]{newtxmath}
%\usepackage{kpfonts}
%\usepackage{mathpazo}
%\usepackage{mathpazo}
%\usepackage{eulervm}
%\usepackage{charter}
%\usepackage[bitstream-charter]{mathdesign}

% ============= chapter/section headings =============
% 
% \setkomafont{chapter}{%
% \renewcommand{\bfdefault}{sb}%
% %\usefont{T1}{qhv}{b}{n}\selectfont
% \fontfamily{put}\bfseries\huge%
% %\rmfamily\huge
% \renewcommand{\bfdefault}{bx}%
% }
% \setkomafont{section}{%
% \renewcommand{\bfdefault}{sb}%
% %\usefont{T1}{qhv}{b}{n}\selectfont
% %\bfseries\Large
% \fontfamily{put}\bfseries\large%
% \renewcommand{\bfdefault}{bx}%
% }
% \setkomafont{subsection}{%
% \renewcommand{\bfdefault}{sb}%
% \fontfamily{put}\bfseries\large%
% \renewcommand{\bfdefault}{bx}%
% }
% \usepackage[grey,avantgarde]{quotchap}% For a nice grey number at each new chapter, also allows for chapter quotes

% ============= text formatting tweaks =============

\usepackage{url,ellipsis}
\usepackage[final=true,step=1]{microtype}
\usepackage{ragged2e}
\clubpenalty = 500
\widowpenalty = 1000
\urlstyle{sf}
\deffootnote[1.5em]{1.5em}{1.5em}{\thefootnotemark \hspace{0.2em}} 
% line spacing:
\usepackage{setspace}
\def\mynormalstretch{1.05}
\setstretch{\mynormalstretch}
\usepackage[nice]{nicefrac}
\usepackage{textcomp}

% ============= tables =============

% TODO: I should use nicetabular from the nicematrix package to make the
% decision tables nicer (e.g. rules that show up properly in pdf readers), but
% that requires a more recent latex installation.

\usepackage{booktabs}
% \renewcommand{\arraystretch}{1.1} % more space between table rows
\usepackage{tabularx}
% \usepackage{colortbl}
\newcommand{\gr}{\cellcolor{gray!20}}
% \usepackage{nicematrix}
% \usetikzlibrary{matrix,positioning,fit,backgrounds,calc}
\usepackage{environ}
% \usepackage{xstring}
% \usepackage{etoolbox}

\NewEnviron{dmatrix}[1]{%
  \medskip
  \begin{center}
  % \setlength{\arrayrulewidth}{1pt} 
    \arrayrulecolor{lightgray}
    \def\arraystretch{1.2} % horizontal padding
    \begin{tabular}{|>{\columncolor{gray!20}}#1|}
      % \arrayrulecolor{lightgray}
      \rowcolor{gray!20}
      \BODY
    \end{tabular}
  \end{center}
  \medskip
}

\NewEnviron{inlinedmatrix}[1]{%
    \arrayrulecolor{lightgray}
    \def\arraystretch{1.1} % horizontal padding
    \begin{tabular}[t]{|>{\columncolor{gray!20}}#1|}
      \rowcolor{gray!20}
      \BODY
    \end{tabular}
}

% \makeatletter
% \tikzset{savecols/.style={execute at end matrix={
%     \xdef#1{\the\pgf@matrix@numberofcolumns}}},
% saverows/.style={execute at end matrix={
%     \xdef#1{\the\pgfmatrixcurrentrow}}}}
% \makeatother
% \tikzset{ 
%     dtable/.style={
%         matrix of nodes,
%         % row sep=-\pgflinewidth,
%         % column sep=-\pgflinewidth,
%         % nodes in empty cells,
%         nodes={draw=gray, align=center, minimum height=1.3em, inner sep=0.5mm, anchor=center},
%         inner sep=0pt, draw,
%         text depth=0.5ex,
%         text height=2ex,
%         % every node/.append style={
%         %   draw=lightgray,
%         % },
%         column 1/.style={
%             nodes={fill=gray!10,}
%         },
%         row 1/.style={
%             nodes={fill=gray!10}
%         }
%     }
% }
% \NewEnviron{dmatrix}{%
%   \begin{center}
%   \begin{tikzpicture}
%    \matrix (m) [dtable,saverows=\rows,savecols=\cols]
%    {
%      \BODY
%    };
%    % \foreach \col in {1,...,\cols} {
%    %   \draw (m-1-\col.north west) -- (m-\rows-\col.south west);
%    %   \ifnum\col=\cols
%    %      \draw (m-1-\col.north east) -- (m-\rows-\col.south east);
%    %   \fi
%    % }
%  \end{tikzpicture}
%   \end{center}
% }

% \AtBeginEnvironment{dmatrix}{\catcode`\&\active}

% ============= page headers =============

% removes the header from odd empty pages at the end of chapters:
\makeatletter
\renewcommand{\cleardoublepage}{
\clearpage\ifodd\c@page\else
\hbox{}
\vspace*{\fill}
\thispagestyle{empty}
\newpage
\fi}

% ============= colors and links =============

\definecolor{linkcol}{rgb}{0,0.1,0.4}
\definecolor{citecol}{rgb}{0,0.2,0.2}
\usepackage[colorlinks=true,
            linkcolor=linkcol,
            urlcolor=linkcol,
            citecolor=citecol]{hyperref}

% ============= citations ==============

\usepackage{natbib}
\bibpunct[: ]{[}{]}{,}{A}{}{,~}
\renewcommand{\cite}[2][]{\citep[#1]{#2}}
\newcommand{\citey}[2][]{\citeyearpar[#1]{#2}}
\newcommand{\citeplain}[2][]{\citealt[#1]{#2}}
\newcommand{\citeyplain}[2][]{\citeyear[#1]{#2}}

% ============= boxes ==============

\usepackage[most]{tcolorbox}
\usepackage{xparse}

%\definecolor{teal}{HTML}{ba5536}
%\definecolor{terra}{HTML}{363237}
\definecolor{teal}{HTML}{34675c}
\definecolor{terra}{HTML}{324851}

% plain box:
\newtcolorbox{justabox}{
  enhanced,
  colback=terra!2!white,
  colframe=terra!80!white,
  boxrule=0.3mm,
  drop small lifted shadow,
  beforeafter skip=\baselineskip,
}

% Example (optional title and "label=ex:foo"):
\NewTColorBox[auto counter,number within=chapter]{example}{d() o}{
  enhanced,
  breakable,
  enhanced jigsaw,
  colback=terra!2!white,
  colframe=terra!80!white,
  colbacktitle=terra!2!white,
  boxrule=0.3mm,
  drop small lifted shadow,
  titlerule=-0.5mm,
  toptitle=2mm,
  beforeafter skip=\baselineskip,
  fonttitle=\upshape\bfseries\sffamily,
  coltitle=terra!90!black,
  fontupper=\normalfont,
  title=Example~\thetcbcounter,
  IfValueTF={#1}{after title={\;(#1)}}{},
  IfValueTF={#2}{#2}{},
}
                                             
% Essay question:                                             
\NewTColorBox[auto counter,number within=chapter]{essay}{}{
  breakable,
  enhanced jigsaw,
  fonttitle=\sffamily\upshape\bfseries,
  coltitle=teal!10!white,
  colback=teal!02!white,
  colbacktitle=teal,
  colframe=teal!70!black,
  boxrule=0.3mm,
  attach boxed title to top left={yshift=-1mm, xshift=1mm},
  beforeafter skip=.9\baselineskip,
  title=Essay Question~\thetcbcounter,
}

% Exercises:                                             
\NewTColorBox[auto counter,number within=chapter]{exercise}{ o m o }{
  % e.g. \begin{exercise}{3} or \begin{exercise}[The Prisoners' Dilemma]{3}
  breakable,
  enhanced jigsaw,
  fonttitle=\sffamily\upshape\bfseries,
  coltitle=teal!10!white,
  colback=teal!02!white,
  colbacktitle=teal,
  colframe=teal!70!black,
  boxrule=0.3mm,
  attach boxed title to top left={yshift=-1mm, xshift=1mm},
  beforeafter skip=.9\baselineskip,
  title=Exercise~\thetcbcounter,
  IfValueTF={#1}{after title={\;(#1) \foreach \n in {1,...,#2}{$\dagger$}\!}}{after title=\;{\foreach \n in {1,...,#2}{$\dagger$}\!}},
  IfValueTF={#3}{#3}{},
}

% important box with title (no number):
\NewTColorBox{genericthm}{m}{%
  enhanced,
  breakable,
  enhanced jigsaw,
  colback=terra!2!white,
  colframe=terra!80!white,
  colbacktitle=terra!2!white,
  boxrule=0.3mm,
  drop small lifted shadow,
  titlerule=-0.5mm,
  toptitle=2mm,
  beforeafter skip=\baselineskip,
  fonttitle=\upshape\bfseries\sffamily,
  coltitle=terra!90!black,
  fontupper=\normalfont,
  title=#1,
}

% Sources and further reading:
\newtcolorbox{sources}{
  enhanced,
  breakable,
  enhanced jigsaw,
  % parbox=false,
  before upper=\setlength{\parskip}{0.5em},
  colback=terra!1!white,
  colframe=terra!10!white,
  boxrule=0.3mm,
  beforeafter skip=\baselineskip,
  titlerule=-0.5mm,
  toptitle=1.3mm,
  fonttitle=\upshape\bfseries\sffamily,
  fontupper=\small,
  colbacktitle=terra!2!white,
  coltitle=terra!30!black,
  % fontupper=\normalfont,
  title=Sources and Further Reading,
}

% custom list format in exercises:
\usepackage[shortlabels]{enumitem} % \begin{enumerate}[(a)] and \itemsep
\newenvironment{exlist}{\vspace{-2mm}\begin{enumerate}[(a)]\itemsep-1.5mm}{\end{enumerate}\vspace{-5mm}}
\newcommand{\beginwithlist}{\vspace{1mm}}


# coding=utf-8

import unittest
import mock

from dmutils.content_loader import ContentLoader


class TestContentLoader(unittest.TestCase):
    def test_a_simple_question(self):
        content = ContentLoader(
          """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          """
              firstQuestion.yml
                question: 'First question'
          """
        )
        self.assertEqual(
            content.getQuestion("firstQuestion").question,
            "First question"
        )

    def test_a_question_with_a_dependency(self):
        content = ContentLoader(
          """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          """
              firstQuestion.yml
                question: 'First question'
                depends:
                    -
                      on: lot
                      being: SCS

          """
        )
        content.filter_questions({
            "lot": "SCS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_a_question_with_a_dependency_that_doesnt_match(self):
        content = ContentLoader(
          """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          """
              firstQuestion.yml
                question: 'First question'
                depends:
                    -
                      on: lot
                      being: SCS

          """
        )
        content.filter_questions({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )

    def test_a_question_which_depends_on_one_of_several_answers(self):
        content = ContentLoader(
          """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          """
              firstQuestion.yml
                question: 'First question'
                depends:
                    -
                      on: lot
                      being:
                       - SCS
                       - SaaS
                       - PaaS

          """
        )
        content.filter_questions({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_a_question_which_depends_on_one_of_several_answers(self):
        content = ContentLoader(
          """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          """
              firstQuestion.yml
                question: 'First question'
                depends:
                    -
                      on: lot
                      being:
                       - SCS
                       - SaaS
                       - PaaS

          """
        )
        content.filter_questions({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )

    def test_a_section_which_has_a_mixture_of_dependencies(self):
        content = ContentLoader(
          """
              -
                name: First section
                questions:
                  - firstQuestion
                  - secondQuestion
              -
                name: Second section
                questions:
                  - firstQuestion
          """,
          """
              firstQuestion.yml
                question: 'First question'
                depends:
                    -
                      on: lot
                      being:
                       - SCS
                       - SaaS
                       - PaaS
              secondQuestion.yml
                question: 'Second question'
                depends:
                    -
                      on: lot
                      being: IaaS

          """
        )
        content.filter_questions({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )
        self.assertEqual(
            len(content.get_question("firstQuestion")),
            None
        )
        self.assertNotEqual(
            len(content.get_question("secondQuestion")),
            None
        )

#!/usr/bin/env python
# coding: utf-8

"""
    django-reversion-compare unittests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test history compare CBV
    
    :copyleft: 2012-2016 by the django-reversion-compare team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import absolute_import, division, print_function


try:
    import django_tools
except ImportError as err:
    msg = (
        "Please install django-tools for unittests"
        " - https://github.com/jedie/django-tools/"
        " - Original error: %s"
    ) % err
    raise ImportError(msg)


from reversion_compare import reversion_api
from .test_utils.test_cases import BaseTestCase
from .models import SimpleModel
from .test_utils.test_data import TestData


class CBViewTest(BaseTestCase):
    """
    unittests for testing reversion_compare.views.HistoryCompareDetailView

    Tests for the basic functions.
    """
    def setUp(self):
        super(CBViewTest, self).setUp()
        test_data = TestData(verbose=False)
        self.item1, self.item2 = test_data.create_Simple_data()

        queryset = reversion_api.get_for_object(self.item1)
        self.version_ids1 = queryset.values_list("pk", flat=True)
        
        queryset = reversion_api.get_for_object(self.item2)
        self.version_ids2 = queryset.values_list("pk", flat=True)

    def test_initial_state(self):
        self.assertTrue(reversion_api.is_registered(SimpleModel))

        self.assertEqual(SimpleModel.objects.count(), 2)
        self.assertEqual(SimpleModel.objects.all()[0].text, "version two")

        self.assertEqual(reversion_api.get_for_object(self.item1).count(), 2)
        self.assertEqual(list(self.version_ids1), [2, 1])
        
        self.assertEqual(list(self.version_ids1), [2, 1])
        self.assertEqual(list(self.version_ids2), [7, 6, 5, 4, 3])
        
    def test_select_compare1(self):
        response = self.client.get("/test_view/%s" % self.item1.pk)
        self.assertContainsHtml(
            response,
            '<input type="submit" value="compare">',
            '<input type="radio" name="version_id1" value="%i" style="visibility:hidden" />' % self.version_ids1[0],
            '<input type="radio" name="version_id2" value="%i" checked="checked" />' % self.version_ids1[0],
            '<input type="radio" name="version_id1" value="%i" checked="checked" />' % self.version_ids1[1],
            '<input type="radio" name="version_id2" value="%i" />' % self.version_ids1[1],
        )
        
    def test_select_compare2(self):
        response = self.client.get("/test_view/%s" % self.item2.pk)
        for i in range(4):
            if i == 0:
                comment = "create v%i" % i
            else:
                comment = "change to v%i" % i

            self.assertContainsHtml(
                response,
                "<td>%s</td>" % comment,
                '<input type="submit" value="compare">',
            )
        
    def test_select_compare_and_diff(self):
        response = self.client.get("/test_view/%s" % self.item1.pk, data={
            "version_id2": self.version_ids1[0],
            "version_id1": self.version_ids1[1]
        })
        self.assertContainsHtml(
            response,
            '<input type="submit" value="compare">',
            '<input type="radio" name="version_id1" value="%i" style="visibility:hidden" />' % self.version_ids1[0],
            '<input type="radio" name="version_id2" value="%i" checked="checked" />' % self.version_ids1[0],
            '<input type="radio" name="version_id1" value="%i" checked="checked" />' % self.version_ids1[1],
            '<input type="radio" name="version_id2" value="%i" />' % self.version_ids1[1],
        )
        self.assertContainsHtml(
            response,
            '<del>- version one</del>',
            '<ins>+ version two</ins>',
            '<blockquote>simply change the CharField text.</blockquote>',  # edit comment
        )
        
    def test_prev_next_buttons(self):
        base_url = "/test_view/%s" % self.item2.pk
        for i in range(4):
            # IDs: 3,4,5,6
            id1 = i+3
            id2 = i+4
            response = self.client.get(
                base_url,
                data={"version_id2": id2, "version_id1": id1}
            )
            self.assertContainsHtml(
                response,
                '<del>- v%i</del>' % i,
                '<ins>+ v%i</ins>' % (i+1),
                '<blockquote>change to v%i</blockquote>' % (i+1),
            )

            next = '<a href="?version_id1=%s&amp;version_id2=%s">next &rsaquo;</a>' % (i+4, i+5)
            prev = '<a href="?version_id1=%s&amp;version_id2=%s">&lsaquo; previous</a>' % (i+2, i+3)

            if i == 0:
                self.assertNotContains(response, "previous")
                self.assertContains(response, "next")
                self.assertContainsHtml(response, next)
            elif i == 3:
                self.assertContains(response, "previous")
                self.assertNotContains(response, "next")
                self.assertContainsHtml(response, prev)
            else:
                self.assertContains(response, "previous")
                self.assertContains(response, "next")
                self.assertContainsHtml(response, prev, next)

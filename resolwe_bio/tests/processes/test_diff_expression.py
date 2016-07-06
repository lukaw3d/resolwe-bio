# pylint: disable=missing-docstring
from resolwe_bio.utils.test import skipDockerFailure, BioProcessTestCase


class DiffExpProcessorTestCase(BioProcessTestCase):

    @skipDockerFailure("Errors with: KeyError: u'mask_file' at "
        "cuff_exp = self.run_processor('cufflinks', inputs)")
    def test_cuffdiff(self):
        genome = self.prepare_genome()
        reads1 = self.prepare_reads('00Hr.fastq.gz')
        reads2 = self.prepare_reads('20Hr.fastq.gz')

        inputs = {'src': 'annotation.gff.gz'}
        annotation = self.run_processor('upload-gff3', inputs)

        inputs = {
            'genome': genome.pk,
            'reads': reads1.pk,
            'gff': annotation.pk,
            'PE_options': {
                'library_type': "fr-unstranded"}}
        aligned_reads_1 = self.run_processor('alignment-tophat2', inputs)

        inputs = {
            'genome': genome.pk,
            'reads': reads2.pk,
            'gff': annotation.pk,
            'PE_options': {
                'library_type': "fr-unstranded"}}
        aligned_reads_2 = self.run_processor('alignment-tophat2', inputs)

        inputs = {
            'alignment': aligned_reads_1.pk,
            'gff': annotation.pk,
            'genome': genome.pk}
        cuff_exp = self.run_processor('cufflinks', inputs)

        inputs = {
            'alignment': aligned_reads_2.pk,
            'gff': annotation.pk,
            'genome': genome.pk}
        cuff_exp2 = self.run_processor('cufflinks', inputs)

        inputs = {
            'expressions': [cuff_exp.pk, cuff_exp2.pk],
            'gff': annotation.pk,
            'genome': genome.pk}
        cuff_merge = self.run_processor('cuffmerge', inputs)

        inputs = {
            'alignment': aligned_reads_1.pk,
            'gff': cuff_merge.pk}
        cuffquant = self.run_processor('cuffquant', inputs)

        inputs = {
            'alignment': aligned_reads_2.pk,
            'gff': cuff_merge.pk}
        cuffquant2 = self.run_processor('cuffquant', inputs)

        inputs = {
            'cuffquant': [cuffquant.pk, cuffquant2.pk],
            'replicates': ['1', '2'],
            'labels': ['g1', 'g2'],
            'gff': cuff_merge.pk}
        cuffdiff = self.run_processor('cuffdiff', inputs)
        self.assertFile(cuffdiff, 'gene_diff_exp', 'cuffdiff_output.gz', compression='gzip')

    @skipDockerFailure("Errors with: ERROR: basic:json value in exp_json not "
        "ObjectId but {u'genes': {u'DPU_G0067108': 0.0, ...}} at "
        "diff_exp = self.run_processor('differentialexpression-bcm', inputs)")
    def test_bayseq_bcm(self):
        expression_1 = self.prepare_expression(f_rc='exp_1_rc.tab.gz', f_exp='exp_1_tpm.tab.gz', f_type="TPM")
        expression_2 = self.prepare_expression(f_rc='exp_2_rc.tab.gz', f_exp='exp_2_tpm.tab.gz', f_type="TPM")

        mappa = self.run_processor("upload-mappability", {"src": "purpureum_mappability_50.tab.gz"})

        inputs = {
            'name': "00vs20",
            'case': [expression_1.pk],
            'control': [expression_2.pk],
            'replicates': ['1', '2'],
            'mappability': mappa.pk}
        diff_exp = self.run_processor('differentialexpression-bcm', inputs)
        self.assertJSON(diff_exp, diff_exp.output['volcano_plot'], '', 'bayseq_volcano.json.gz')

    @skipDockerFailure("Errors with: ERROR: basic:json value in exp_json not "
        "ObjectId but {u'genes': {u'DPU_G0067108': 0.0, ...}} at "
        "diff_exp = self.run_processor('differentialexpression-deseq2', inputs)")
    def test_deseq2(self):
        expression_1 = self.prepare_expression(f_rc='exp_1_rc.tab.gz', f_exp='exp_1_tpm.tab.gz', f_type="TPM")
        expression_2 = self.prepare_expression(f_rc='exp_2_rc.tab.gz', f_exp='exp_2_tpm.tab.gz', f_type="TPM")

        inputs = {
            'case': [expression_1.pk],
            'control': [expression_2.pk]
        }

        diff_exp = self.run_processor('differentialexpression-deseq2', inputs)
        self.assertFile(diff_exp, "diffexp", 'diffexp_deseq2.tab.gz', compression='gzip')

    @skipDockerFailure("Errors with: ERROR: basic:json value in exp_json not "
        "ObjectId but {u'genes': u'236613_at': 7.40..., ...}} at "
        "diff_exp = self.run_processor('differentialexpression-limma', inputs)")
    def test_limma(self):
        expression_1 = self.prepare_expression(f_exp='exp_limma_1.tab.gz', f_type="Log2")
        expression_2 = self.prepare_expression(f_exp='exp_limma_2.tab.gz', f_type="Log2")
        expression_3 = self.prepare_expression(f_exp='exp_limma_3.tab.gz', f_type="Log2")
        expression_4 = self.prepare_expression(f_exp='exp_limma_4.tab.gz', f_type="Log2")

        inputs = {
            'case': [expression_1.pk, expression_2.pk],
            'control': [expression_3.pk, expression_4.pk]
        }

        diff_exp = self.run_processor('differentialexpression-limma', inputs)
        self.assertFile(diff_exp, "diffexp", 'diffexp_limma.tab.gz', compression='gzip')
